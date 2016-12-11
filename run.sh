#!/bin/bash
set -e

echo "starting..."

_term() {
  echo "received SIGTERM, closing"
  kill -TERM "$child" 2>/dev/null
}

trap _term SIGTERM

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

postmap /etc/postfix/virtual

#printf "\n\n# Postfix config:"
#postconf

echo "starting postfix..."
/usr/sbin/postfix -c /etc/postfix start
echo "starting rsyslogd..."
rsyslogd -n &

child=$!

echo "waiting indefinitely for SIGTERM..."
wait "$child"
