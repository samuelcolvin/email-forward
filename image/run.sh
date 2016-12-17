#!/bin/bash
set -e

_term() {
  echo "received termination signal, closing..."
  exit
}

trap _term SIGTERM SIGINT

if [ -z "$MY_DOMAIN" ]
then echo "\$MY_DOMAIN is required but empty or unset"; exit 1
fi

if [ -z "$FORWARD_TO" ]
then echo "\$FORWARD_TO is required but empty or unset"; exit 1
fi

if [ -z "$FORWARDED_DOMAINS" ]
then echo "\$FORWARDED_DOMAINS is required but empty or unset"; exit 1
fi

printf "\n\n\n=================== starting docker-postfix ===================\n"

echo "bash --version: $(bash --version)"

echo "uname -a: $(uname -a)"

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

# create "/domains" and "/etc/postfix/virtual" to contain domain and alias information
rm /etc/postfix/virtual 2>/dev/null || true
for domain in $FORWARDED_DOMAINS; do
  echo "$domain -" >> /domains
  echo "@$domain $FORWARD_TO" >> /etc/postfix/virtual
done
# run postmap to create the berkley db files for domains and aliases
postmap /domains
postmap /etc/postfix/virtual

# domains for which postfix is going to accept emails and forwarding aliases
postconf -e virtual_alias_domains=hash:/domains
postconf -e virtual_alias_maps=hash:/etc/postfix/virtual

# force encryption
postconf -e smtp_tls_security_level=encrypt
postconf -e smtp_enforce_tls=yes

# set host name and domain
postconf -e myhostname=mail.$MY_DOMAIN
postconf -e mydomain=$MY_DOMAIN

# Add postfix configuration parameters for postsrsd
postconf -e sender_canonical_maps=tcp:127.0.0.1:10001
postconf -e sender_canonical_classes=envelope_sender
postconf -e recipient_canonical_maps=tcp:127.0.0.1:10002
postconf -e recipient_canonical_classes=envelope_recipient

# postfix queue settings
postconf -e maximal_queue_lifetime=4h
postconf -e bounce_queue_lifetime=4h
postconf -e minimal_backoff_time=55m
postconf -e maximal_backoff_time=70m
postconf -e queue_run_delay=5m

chown root:postfix /var/spool/postfix
chown root:postfix /var/spool/postfix/pid

#printf "\n\n# Postfix config:\n==============================\n"
#postconf
#printf "==============================\n\n\n"

echo "(re)starting postsrd..."
killall postsrsd 2>/dev/null || true
postsrsd -d mail.$MY_DOMAIN -s /etc/postsrsd.secret &

echo "(re)starting postfix..."
postfix stop 2>/dev/null || true
postfix -c /etc/postfix start
postfix status

echo "(re)starting rsyslogd..."
# try deleting the pid and killing rsyslogd in case it was started before
rm /var/run/rsyslogd.pid 2>/dev/null || true
killall rsyslogd 2>/dev/null || true
rsyslogd -n &

sleep_time=600
echo "starting monitoring loop with $((sleep_time / 60)) min heartbeat..."
runcount=0
while true; do
  runcount=$((runcount+1))
  /memory-json.sh $runcount
  postqueue -j
  sleep $sleep_time &
  wait $!
done
