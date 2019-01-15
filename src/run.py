#!/usr/bin/env python3.7
import asyncio
import logging
import os
import re
import smtplib

import aiodns
from aiosmtpd.controller import Controller
from async_timeout import timeout

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger('email-forward')
logger.setLevel(logging.INFO)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(log_handler)

sentry_logging = LoggingIntegration(
    level=logging.INFO,          # Capture info and above as breadcrumbs
    event_level=logging.WARNING  # Send errors as events
)
s = sentry_sdk.init(integrations=[sentry_logging])
forward_to = os.environ['FORWARD_TO']
_, forward_to_host = forward_to.split('@', 1)
forward_port = 465


class Handler:
    def __init__(self):
        self.resolver = aiodns.DNSResolver(nameservers=('1.1.1.1', '1.0.0.1'))

    async def handle_DATA(self, server, session, envelope):
        with sentry_sdk.configure_scope() as scope:
            scope.set_extra('server', server)
            scope.set_extra('session', session)
            scope.set_extra('envelope', envelope)
            try:
                await self.forward_mail(session, envelope)
            except Exception as exc:
                logger.info('email from "%s" > %s, error: %s', envelope.mail_from, envelope.rcpt_tos, exc)
                sentry_sdk.capture_exception(exc)
            else:
                logger.info('email from "%s" > %s', envelope.mail_from, envelope.rcpt_tos)
            return '250 OK'

    async def forward_mail(self, session, envelope):
        content = envelope.content
        lines = content.splitlines(keepends=True)
        # Look for the last header
        i = 0
        ending = b'\r\n'
        for line in lines:
            if re.match(br'\r\n|\r|\n', line):
                ending = line
                break
            i += 1
        peer = session.peer[0].encode('ascii')
        lines.insert(i, b'X-Peer: %s%s' % (peer, ending))
        content = b''.join(lines)

        with timeout(2):
            results = await self.resolver.query(forward_to_host, 'MX')
        mx_hosts = [r[1] for r in sorted((r.priority, r.host) for r in results)]

        with timeout(10):
            await loop.run_in_executor(None, self.sendmail, mx_hosts, envelope.mail_from, content)

    def sendmail(self, mx_hosts, mail_from, content):
        last_error = RuntimeError('no mx hosts to send email to')
        for mx_host in mx_hosts:
            try:
                with smtplib.SMTP_SSL(mx_host, forward_port) as smtp:
                    smtp.sendmail(mail_from, [forward_to], content)
            except smtplib.SMTPRecipientsRefused:
                # all mail was refused, but it got to the server
                return
            except Exception as e:
                last_error = e
            else:
                # send succeeded
                logger.info('email successfully sent to %s', mx_host)
                return
        raise last_error


if __name__ == '__main__':
    handler = Handler()
    port = int(os.getenv('PORT') or 25)
    logger.info('starting SMTP server on %s, forwarding to %s', port, forward_to)
    controller = Controller(handler, hostname='0.0.0.0', port=port)
    controller.start()

    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
