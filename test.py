#!/usr/bin/env python3
import os
import smtplib
import sys
from email.mime.text import MIMEText


def main():
    if len(sys.argv) < 2:
        return 'wrong number of arguments, please provide email address'

    email = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == 'local':
        mx_host = 'localhost'
        port = 8025
    else:
        mx_host = os.environ['HOST_NAME']
        port = 0

    msg = MIMEText('this is the message')
    msg['Subject'] = 'testing'
    msg['From'] = 'testing@example.com'
    msg['To'] = f'{email}'

    print(f'connecting to mail server "{mx_host}"...')
    with smtplib.SMTP(mx_host, port, local_hostname='testing.example.com') as smtp:
        print('starttls:', smtp.starttls())
        print('noop:', smtp.noop())
        print('helo:', smtp.helo())
        # print('ehlo:', smtp.ehlo())
        # print('mail:', smtp.mail('mail-server-test@example.com'))
        # print(f'rcpt ({email}):', smtp.rcpt(email))
        # print('rcpt (testing_example.com):', smtp.rcpt('testing_example.com'))
        smtp.send_message(msg)


if __name__ == '__main__':
    err = main()
    if err:
        print(err, file=sys.stderr)
        sys.exit(1)

