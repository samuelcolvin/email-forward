#!/usr/bin/env python3.7
import asyncio
import os
from smtplib import SMTP_SSL

from aiosmtpd.controller import Controller
from devtools import debug

import sentry_sdk
sentry_sdk.init()


class Handler:
    def __init__(self):
        self.forward_to = os.environ['FORWARD_TO']
        self.password = os.environ['FORWARD_PASSWORD']

    async def handle_DATA(self, server, session, envelope):
        with sentry_sdk.configure_scope() as scope:
            scope.set_extra('server', server)
            scope.set_extra('session', session)
            scope.set_extra('envelope', envelope)
            await self.send_email(envelope)
            return '250 Message accepted for delivery'

    async def send_email(self, envelope):
        print(f'email from "{envelope.mail_from}" > {envelope.rcpt_tos}')
        try:
            content = envelope.content.decode('utf8', errors='replace')
            with SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.forward_to, self.password)
                smtp.sendmail(envelope.mail_from, envelope.rcpt_tos, content)
        except Exception as exc:
            sentry_sdk.capture_exception(exc)


if __name__ == '__main__':
    handler = Handler()
    port = int(os.getenv('PORT') or 25)
    print('starting SMTP server on', port)
    controller = Controller(handler, hostname='0.0.0.0', port=port)
    controller.start()

    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
