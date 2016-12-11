FROM alpine:3.4
MAINTAINER Samuel Colvin <s@muelcolvin.com>

RUN apk add --no-cache --update postfix ca-certificates rsyslog bash \
 && (rm "/tmp/"* 2>/dev/null || true) && (rm -rf /var/cache/apk/* 2>/dev/null || true)

COPY rsyslog.conf /etc/rsyslog.conf
COPY postfix_virtual /etc/postfix/virtual
COPY run.sh /run.sh
RUN chmod +x /run.sh

USER root

EXPOSE 25
EXPOSE 465
EXPOSE 587
ENTRYPOINT ["/run.sh"]
