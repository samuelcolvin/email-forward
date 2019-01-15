#!/usr/bin/env python3
import smtplib
import sys
from email.mime.text import MIMEText


def main():
    try:
        from dns import resolver
    except ImportError:
        resolver = None
        return 'dnspython not installed, use `pip install dnspython`'

    if len(sys.argv) != 2:
        return 'wrong number of arguments, please provide email address'

    email = sys.argv[1]
    mailbox, host = email.split('@', 1)

    if host == 'localhost':
        mx_host = 'localhost'
        port = 8025
    else:
        answers = list(resolver.query(host, 'MX'))
        mx_host = answers[0].exchange.to_text()
        port = 0

    msg = MIMEText('this is the message')
    msg['Subject'] = 'testing'
    msg['From'] = 'testing@example.com'
    msg['To'] = f'{email}'

    print(f'connecting to mail server "{mx_host}"...')
    with smtplib.SMTP(mx_host, port) as smtp:
        print('noop:', smtp.noop())
        print('helo:', smtp.helo())
        # print('mail:', smtp.mail('mail-server-test@example.com'))
        # print(f'rcpt ({email}):', smtp.rcpt(email))
        # print('rcpt (testing_example.com):', smtp.rcpt('testing_example.com'))
        smtp.send_message(msg)


if __name__ == '__main__':
    err = main()
    if err:
        print(err, file=sys.stderr)
        sys.exit(1)

