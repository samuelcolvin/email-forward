#!/usr/bin/env python3.7
import os
import smtplib
import sys
from email.mime.text import MIMEText

if 'local' in sys.argv:
    print('checking local container')
    host = 'localhost'
    port = 8025

else:
    host = 'mail.{}'.format(os.environ['MY_DOMAIN'])
    port = 0

domains = os.environ['FORWARDED_DOMAINS'].split(' ')

msg = MIMEText('this is the message')
msg['Subject'] = 'testing'
msg['From'] = 'testing@testing.com'
msg['To'] = 'whatever@{}'.format(domains[0])

print('connecting to "{}"...'.format(host))
with smtplib.SMTP(host, port) as smtp:
    print('noop:', smtp.noop())
    print('helo:', smtp.helo())
    # print('mail:', smtp.mail('testing@testing.com'))
    # for domain in domains:
    #     print('rcpt {} (should succeed):'.format(domain), smtp.rcpt('testing@{}'.format(domain)))
    print('rcpt example.com (should fail): ', smtp.rcpt('testing@example.com'))
    smtp.send_message(msg)
