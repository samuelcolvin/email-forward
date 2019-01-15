#!/usr/bin/env python3.7
import base64
import os
import secrets
import smtpd
import smtplib
import re
import ssl
from datetime import datetime
from pathlib import Path
from time import sleep

import boto3
from dns import resolver

from .utils import TLSChannel, logger, with_sentry

local_port = int(os.getenv('PORT') or 8025)
commit = os.getenv('COMMIT') or '-'

forward_to = os.environ['FORWARD_TO']
_, forward_to_host = forward_to.split('@', 1)

allowed_domains = set(filter(None, os.getenv('FORWARDED_DOMAINS', '').split(' ')))

ssl_crt_file = Path('./ssl.crt')
if not ssl_crt_file.exists():
    ssl_crt_file.write_text(base64.b64decode(os.environ['SSL_CRT'].encode()).decode())
ssl_key_file = Path('./ssl.key')
if not ssl_key_file.exists():
    ssl_key_file.write_text(base64.b64decode(os.environ['SSL_KEY'].encode()).decode())

s3 = boto3.resource('s3')
s3_bucket = os.environ.get('AWS_BUCKET_NAME')


class SMTPServer(smtpd.SMTPServer):
    channel_class = TLSChannel

    def __init__(self):
        logger.info('starting SMTP server on %s\nforwarding to %s\nallowed domains: %s\ncommit: "%s"',
                    local_port, forward_to, allowed_domains, commit)

        super().__init__(('0.0.0.0', local_port), None)

        self.ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_ctx.load_cert_chain(certfile=str(ssl_crt_file), keyfile=str(ssl_key_file))
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE

    def handle_accepted(self, conn, addr):
        logger.info('incoming connection from %s:%s', *addr)
        super().handle_accepted(conn, addr)

    @with_sentry
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        logger.info('forwarding "%s" > %s', mailfrom, ', '.join(rcpttos))
        if self.allow_address(*rcpttos):
            try:
                self.send_email(peer, mailfrom, data)
            finally:
                self.record_s3(mailfrom, data)
        else:
            logger.warning('forwarding not permitted for any of %s', rcpttos)

    def send_email(self, peer, mailfrom, data):
        lines = data.splitlines(keepends=True)
        # Look for the last header
        i = 0
        ending = b'\r\n'
        for line in lines:
            if re.match(br'\r\n|\r|\n', line):
                ending = line
                break
            i += 1
        peer = peer[0].encode('ascii')
        lines.insert(i, b'X-Peer: %s%s' % (peer, ending))
        content = b''.join(lines)

        send_error = None
        mx_hosts = sorted((r.preference, r.exchange.to_text()) for r in resolver.query(forward_to_host, 'MX'))
        for _, mx_host in mx_hosts:
            try:
                with smtplib.SMTP(mx_host, 25, timeout=10) as smtp:
                    smtp.starttls()
                    smtp.sendmail(mailfrom, [forward_to], content)
            except smtplib.SMTPException as e:
                logger.warning('%s on %s, not trying further hosts', e.__class__.__name__, mx_host)
                return
            except Exception as e:
                logger.warning('error with host %s %s: %s', mx_host, e.__class__.__name__, e)
                send_error = send_error or e
            else:
                # send succeeded
                return
            sleep(1)
        assert send_error, 'no MX hosts found to send email to'
        raise send_error

    def record_s3(self, mailfrom, data):
        if s3_bucket:
            n = datetime.utcnow()
            key = f'{n:%Y-%m}/{n:%Y-%m-%dT%H-%M-%S}_{mailfrom}_{secrets.token_hex(5)}.msg'
            s3.Bucket(s3_bucket).put_object(Key=key, Body=data)
        else:
            logger.warning('s3_bucket not set, not saving to S3')

    @staticmethod
    def allow_address(*addresses):
        return any(r.split('@', 1)[1] in allowed_domains for r in addresses)
