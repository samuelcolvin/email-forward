#!/usr/bin/env python3.7
import asyncore

from email_forward.main import SMTPServer

if __name__ == '__main__':
    server = SMTPServer()
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass
