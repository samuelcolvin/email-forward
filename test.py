import smtplib

from email.mime.text import MIMEText

msg = MIMEText('this is the message')
msg['Subject'] = 'testing'
msg['From'] = 'testing@gaugemore.com'
msg['To'] = 'whatever@scolvin.com'

with smtplib.SMTP('mail.muelcolvin.com') as smtp:
    print('noop:', smtp.noop())
    print('helo:', smtp.helo())
    print('mail:', smtp.mail('testing@testing.com'))
    print('rcpt testing@scolvin.com:    ', smtp.rcpt('testing@scolvin.com'))
    print('rcpt testing@muelcolvin.com: ', smtp.rcpt('testing@muelcolvin.com'))
    print('rcpt testing@gaugemore.com:  ', smtp.rcpt('testing@gaugemore.com'))
    print('rcpt testing@helpmanual.io:  ', smtp.rcpt('testing@helpmanual.io'))
    print('rcpt testing@example.com:    ', smtp.rcpt('testing@example.com'))
    # smtp.send_message(msg)
