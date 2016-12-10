import smtplib
import time

from email.mime.text import MIMEText

msg = MIMEText('this is the message')
msg['Subject'] = 'testing'
msg['From'] = 'testing@gaugemore.com'
msg['To'] = 'whatever@scolvin.com'

with smtplib.SMTP('localhost', port=8587) as smtp:
    print('noop:', smtp.noop())
    print('sleeping 1')
    time.sleep(1)
    print('helo:', smtp.helo())
    print('help:', smtp.help())
    # s.send_message(msg)
