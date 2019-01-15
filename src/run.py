#!/usr/bin/env python3.7
import asyncore
import asynchat
import base64
import os
import logging
import smtpd
import smtplib
import re
import ssl
import traceback
from pathlib import Path

import sentry_sdk
from dns import resolver
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger('email-forward')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt='%(message)s'))
logger.addHandler(handler)

sentry_logging = LoggingIntegration(
    level=logging.INFO,          # Capture info and above as breadcrumbs
    event_level=logging.WARNING  # Send errors as events
)
sentry_sdk.init(integrations=[sentry_logging])
forward_to = os.environ['FORWARD_TO']
_, forward_to_host = forward_to.split('@', 1)

ssl_crt_file = Path('./ssl.crt')
if not ssl_crt_file.exists():
    ssl_crt_file.write_text(base64.b64decode(os.environ['SSL_CRT'].encode()).decode())
ssl_key_file = Path('./ssl.key')
if not ssl_key_file.exists():
    ssl_key_file.write_text(base64.b64decode(os.environ['SSL_KEY'].encode()).decode())


class TLSSMTPChannel(smtpd.SMTPChannel):
    """
    Roughly from https://github.com/tintinweb/python-smtpd-tls/blob/master/smtpd_tls.py
    """
    def smtp_EHLO(self, arg):
        """
        unchanged from super method, except for 250-STARTTLS lines
        """
        if not arg:
            self.push('501 Syntax: EHLO hostname')
            return
        # See issue #21783 for a discussion of this behavior.
        if self.seen_greeting:
            self.push('503 Duplicate HELO/EHLO')
            return
        self._set_rset_state()
        self.seen_greeting = arg
        self.extended_smtp = True
        self.push('250-%s' % self.fqdn)

        # changed {
        if not isinstance(self.conn, ssl.SSLSocket):
            self.push('250-STARTTLS')
        # }

        if self.data_size_limit:
            self.push('250-SIZE %s' % self.data_size_limit)
            self.command_size_limits['MAIL'] += 26
        if not self._decode_data:
            self.push('250-8BITMIME')
        if self.enable_SMTPUTF8:
            self.push('250-SMTPUTF8')
            self.command_size_limits['MAIL'] += 10
        self.push('250 HELP')
        # if arg and not self.seen_greeting and not isinstance(self.conn, ssl.SSLSocket):
        if not isinstance(self.conn, ssl.SSLSocket):
            self.push('250-STARTTLS')

    def smtp_STARTTLS(self, arg):
        if arg:
            self.push('501 Syntax error (no parameters allowed)')
        elif not isinstance(self.conn, ssl.SSLSocket):
            self.push('220 Ready to start TLS')
            self.conn.settimeout(30)
            self.conn = self.smtp_server.ssl_ctx.wrap_socket(self.conn, server_side=True)
            self.conn.settimeout(None)
            # re-init channel
            asynchat.async_chat.__init__(self, self.conn, self._map)
            self.received_lines = []
            self.smtp_state = self.COMMAND
            self.seen_greeting = 0
            self.mailfrom = None
            self.rcpttos = []
            self.received_data = ''
            logger.debug('peer: %r - negotiated TLS: %r', self.addr, self.conn.cipher())
        else:
            self.push('454 TLS not available due to temporary reason')


class SMTPServer(smtpd.SMTPServer):
    channel_class = TLSSMTPChannel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_ctx.load_cert_chain(certfile=str(ssl_crt_file), keyfile=str(ssl_key_file))

    def handle_accepted(self, conn, addr):
        logger.info('incoming connection from %s:%s', *addr)
        super().handle_accepted(conn, addr)

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        with sentry_sdk.configure_scope() as scope:
            scope.set_extra('peer', peer)
            scope.set_extra('mailfrom', mailfrom)
            scope.set_extra('rcpttos', rcpttos)
            scope.set_extra('data', data)
            scope.set_extra('kwargs', kwargs)
            logger.info('forwarding "%s" > %s', mailfrom, rcpttos)
            try:
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
                self.deliver(mailfrom, content)
            except Exception as e:
                logger.warning('forwarding "%s" > %s, error %s: %s', mailfrom, rcpttos, e.__class__.__name__, e)
                sentry_sdk.capture_exception(e)
                traceback.print_exc()

    def deliver(self, mailfrom, content):
        last_error = RuntimeError('no mx hosts to send email to')
        mx_hosts = sorted((r.preference, r.exchange.to_text()) for r in resolver.query(forward_to_host, 'MX'))
        for _, mx_host in mx_hosts:
            try:
                with smtplib.SMTP(mx_host, 25, timeout=10) as smtp:
                    smtp.starttls()
                    smtp.sendmail(mailfrom, [forward_to], content)
            except smtplib.SMTPRecipientsRefused as e:
                logger.warning('SMTPRecipientsRefused: %s', e.recipients)
                return
            except Exception as e:
                logger.info('error with host %s %s: %s', mx_host, e.__class__.__name__, e)
                last_error = e
            else:
                # send succeeded
                return
        raise last_error


if __name__ == '__main__':
    local_port = int(os.getenv('PORT') or 8025)
    commit = os.getenv('COMMIT', '-')

    print(f'starting SMTP server on {local_port}, forwarding to {forward_to}, commit: "{commit}"')
    server = SMTPServer(('0.0.0.0', local_port), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass
