#!/usr/bin/env python3.7
import base64
import hashlib
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
hostname = os.getenv('HOST_NAME')


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
        self.start_ssl = False

    def handle_accepted(self, conn, addr):
        self.start_ssl = False
        super().handle_accepted(conn, addr)

    @with_sentry
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        m = re.search(b'^Message-ID: <(.+?)>', data, flags=re.M)
        if m:
            # use md5 so we get a unique id without it being 100 chars long
            msg_id = hashlib.md5(m.group(1)).hexdigest()[:10]
        else:
            msg_id = 'unknown-' + secrets.token_hex(5)
        msg_ref = f'{mailfrom}-{msg_id}'

        try:
            if self.allow_address(*rcpttos):
                response = self.forward_email(peer, mailfrom, data)
            else:
                return '454 forwarding not permitted'
            logger.info('msg-ref=%s rcpt=%s size=%d ssl=%r response="%s"',
                        msg_ref, ', '.join(rcpttos), len(data), self.start_ssl, response)
            return response
        finally:
            self.record_s3(msg_id, data)

    def forward_email(self, peer, mailfrom, data) -> str:
        lines = data.splitlines(keepends=True)
        # Look for the last header
        i = 0
        ending = b'\r\n'
        for line in lines:
            if re.match(br'\r\n|\r|\n', line):
                ending = line
                break
            i += 1
        peer_address = peer[0].encode('ascii')
        lines.insert(i, b'X-Peer: %s%s' % (peer_address, ending))
        content = b''.join(lines)

        send_error = None
        mx_hosts = sorted((r.preference, r.exchange.to_text()) for r in resolver.query(forward_to_host, 'MX'))
        for _, mx_host in mx_hosts:
            try:
                with smtplib.SMTP(mx_host, 25, local_hostname=hostname, timeout=10) as smtp:
                    if self.start_ssl:
                        # match behaviour of in coming connection
                        smtp.starttls()
                    smtp.sendmail(mailfrom, [forward_to], content)
            except smtplib.SMTPResponseException as e:
                status = f'{e.smtp_code} {e.smtp_error.decode()}'
                # 421 is "unsolicited mail response", gmail replies with this regularly
                if e.smtp_code != 421:
                    logger.warning('%s SMTP response from %s: %s', e.smtp_code, mx_host, exc_info=True)
                return status
            except Exception as e:
                logger.warning('error with host %s %s: %s', mx_host, e.__class__.__name__, e)
                send_error = send_error or e
            else:
                # send succeeded
                return '250 OK'
            sleep(1)
        logger.error('error while forwarding email', exc_info=send_error, extra={'mx_hosts': mx_hosts})
        return '451 temporarily unable to forward email'

    def record_s3(self, msg_ref, data):
        if s3_bucket:
            n = datetime.utcnow()
            key = f'{n:%Y-%m}/{n:%Y-%m-%dT%H-%M-%S}_{msg_ref}.msg'
            s3.Bucket(s3_bucket).put_object(Key=key, Body=data)
        else:
            logger.warning('s3_bucket not set, not saving to S3')

    @staticmethod
    def allow_address(*addresses):
        return any(r.split('@', 1)[1] in allowed_domains for r in addresses)
