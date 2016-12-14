#!/usr/bin/env python3
import smtplib
import sys

from email.mime.text import MIMEText

msg = MIMEText('this is the message')
msg['Subject'] = 'testing'
msg['From'] = 'testing@gaugemore.com'
msg['To'] = 'whatever@scolvin.com'

host = 'mail.muelcolvin.com'
port = 0  # default

if 'local' in sys.argv:
    print('checking local container')
    host = 'localhost'
    port = 8025

with smtplib.SMTP(host, port) as smtp:
    print('noop:', smtp.noop())
    print('helo:', smtp.helo())
    print('mail:', smtp.mail('testing@testing.com'))
    print('rcpt testing@scolvin.com:    ', smtp.rcpt('testing@scolvin.com'))
    print('rcpt testing@muelcolvin.com: ', smtp.rcpt('testing@muelcolvin.com'))
    print('rcpt testing@gaugemore.com:  ', smtp.rcpt('testing@gaugemore.com'))
    print('rcpt testing@helpmanual.io:  ', smtp.rcpt('testing@helpmanual.io'))
    print('rcpt testing@example.com:    ', smtp.rcpt('testing@example.com'))
    # smtp.send_message(msg)
