#!/usr/bin/env python3.7
import asyncore
import os
import logging
import smtpd
import smtplib
import re
import traceback


import sentry_sdk
from dns import resolver
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger('email-forward')
logger.setLevel(logging.INFO)

sentry_logging = LoggingIntegration(
    level=logging.INFO,          # Capture info and above as breadcrumbs
    event_level=logging.WARNING  # Send errors as events
)
sentry_sdk.init(integrations=[sentry_logging])
forward_to = os.environ['FORWARD_TO']
_, forward_to_host = forward_to.split('@', 1)


class SMTPServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        with sentry_sdk.configure_scope() as scope:
            scope.set_extra('peer', peer)
            scope.set_extra('mailfrom', mailfrom)
            scope.set_extra('rcpttos', rcpttos)
            scope.set_extra('data', data)
            scope.set_extra('kwargs', kwargs)
            logger.info('forwarding "%s" > "%s"', mailfrom, rcpttos)
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
                logger.warning('forwarding "%s" > "%s", error %s: %s', mailfrom, rcpttos, e.__class__.__name__, e)
                sentry_sdk.capture_exception(e)
                traceback.print_exc()

    def deliver(self, mailfrom, content):
        last_error = RuntimeError('no mx hosts to send email to')
        mx_hosts = sorted((r.preference, r.exchange.to_text()) for r in resolver.query(forward_to_host, 'MX'))
        for _, mx_host in mx_hosts:
            try:
                with smtplib.SMTP(mx_host, 25, timeout=10) as smtp:
                    smtp.sendmail(mailfrom, [forward_to], content)
                # with smtplib.SMTP_SSL(*self._remoteaddr, timeout=5) as smtp:
                #     smtp.sendmail(mailfrom, [forward_to], content)
            except smtplib.SMTPRecipientsRefused as e:
                logger.warning('SMTPRecipientsRefused: %s', e.recipients)
                return
            except Exception as e:
                logger.info('error with host %s, %s: %s', mx_host, e.__class__.__name__, e)
                last_error = e
            else:
                # send succeeded
                logger.info('email successfully sent to %s', mx_host)
                return
        raise last_error


if __name__ == '__main__':
    local_port = int(os.getenv('PORT') or 25)
    print(f'starting SMTP server on {local_port}, forwarding to {forward_to}')
    server = SMTPServer(('0.0.0.0', local_port), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass
