#!/usr/bin/env python3.7
import asyncio

import toml
from aiosmtpd.controller import Controller
from devtools import debug


class Handler:
    def __init__(self, config):
        self.config = config
        debug(config)

    async def handle_DATA(self, server, session, envelope):
        print('Message from %s' % envelope.mail_from)
        print('Message for %s' % envelope.rcpt_tos)
        print('Message data:\n')
        debug(envelope.content.decode('utf8', errors='replace'))
        print('End of message')
        return '250 Message accepted for delivery'


if __name__ == '__main__':
    with open('config.toml') as f:
        config = toml.load(f)
    handler = Handler(config)
    print('running on port 8025')
    controller = Controller(handler, hostname='127.0.0.1', port=8025)
    controller.start()

    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
