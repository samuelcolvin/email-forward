#!/bin/bash
set -e

_term() {
  echo "received termination signal, closing..."
  exit
}

trap _term SIGTERM SIGINT

echo "bash version:"
bash --version

echo "system version:"
uname -a

echo "settings up postfix..."

# Disable SMTPUTF8, because libraries (ICU) are missing in alpine
postconf -e smtputf8_enable=no

# Update aliases database. It's not used, but postfix complains if the .db file is missing
postalias /etc/postfix/aliases

# Disable local mail delivery
postconf -e mydestination=
# Don't relay for any domains
postconf -e relay_domains=

# Reject invalid HELOs
postconf -e smtpd_delay_reject=yes
postconf -e smtpd_helo_required=yes
#postconf -e "smtpd_helo_restrictions=reject_unknown_sender_domain,eject_unknown_helo_hostname,reject_invalid_helo_hostname,permit"
postconf -e "smtpd_helo_restrictions=reject_unknown_sender_domain,reject_invalid_helo_hostname,permit"

# domains for which postfix is going to accept emails
postconf -e "virtual_alias_domains=scolvin.com muelcolvin.com gaugemore.com helpmanual.io"
postconf -e virtual_alias_maps=hash:/etc/postfix/virtual

# force encryption
postconf -e smtp_tls_security_level=encrypt
postconf -e smtp_enforce_tls=yes

# set host name and domain
postconf -e myhostname=mail.muelcolvin.com
postconf -e mydomain=muelcolvin.com

postmap /etc/postfix/virtual

#printf "\n\n# Postfix config:\n==============================\n"
#postconf
#printf "==============================\n\n\n"

echo "starting postfix..."
/usr/sbin/postfix -c /etc/postfix start
echo "starting rsyslogd..."
rsyslogd -n &

echo "starting monitoring loop with 10 min heartbeat..."
runcount=0
while true; do
  runcount=$((runcount+1))
  echo "running $runcount"
  top -n 1 -b | head
  sleep 600
done
