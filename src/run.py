#!/usr/bin/env python3.7
import asyncio
import logging
import os
import re
from smtplib import SMTP_SSL

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Proxy
from devtools import debug

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,        # Capture info and above as breadcrumbs
    event_level=logging.INFO   # Send errors as events
)
s = sentry_sdk.init(integrations=[sentry_logging])
forward_to = os.environ['FORWARD_TO']


class Handler(Proxy):
    async def handle_DATA(self, server, session, envelope):
        with sentry_sdk.configure_scope() as scope:
            scope.set_extra('server', server)
            scope.set_extra('session', session)
            scope.set_extra('envelope', envelope)
            try:
                # r = await super().handle_DATA(server, session, envelope)
                await self.send_direct(session, envelope)
            except Exception as exc:
                print(f'email from "{envelope.mail_from}" > {envelope.rcpt_tos}, error:', exc)
                sentry_sdk.capture_exception(exc)
            else:
                print(f'email from "{envelope.mail_from}" > {envelope.rcpt_tos}')
            return '250 OK'

    async def send_direct(self, session, envelope):
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

        with SMTP_SSL(self._hostname, self._port) as smtp:
            smtp.sendmail(envelope.mail_from, [forward_to], content)


if __name__ == '__main__':
    handler = Handler('alt1.gmail-smtp-in.l.google.com', 465)
    port = int(os.getenv('PORT') or 25)
    print(f'starting SMTP server on {port}, forwarding to {forward_to}')
    controller = Controller(handler, hostname='0.0.0.0', port=port)
    controller.start()

    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
