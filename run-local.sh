#!/usr/bin/env bash
docker pull samuelcolvin/postfix-forward
docker run -t -i --rm=true -p=8025:25 \
-e "MY_DOMAIN=$MY_DOMAIN" -e "FORWARD_TO=$FORWARD_TO" -e "FORWARDED_DOMAINS=$FORWARDED_DOMAINS" \
samuelcolvin/postfix-forward $@
