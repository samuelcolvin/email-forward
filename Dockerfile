FROM alpine:3.4
MAINTAINER Samuel Colvin <s@muelcolvin.com>

ENV POSTSRSD_VERSION 1.4
RUN build_packages="wget build-base linux-headers cmake" \
 && runtime_packages="postfix ca-certificates rsyslog bash" \
 && apk --update --no-cache add ${build_packages} ${runtime_packages} \
 && cd /tmp \
 && wget https://github.com/roehling/postsrsd/archive/${POSTSRSD_VERSION}.zip -O postsrsd.zip \
 && unzip postsrsd.zip \
 && cd /tmp/postsrsd-${POSTSRSD_VERSION} \
 && make \
 && make install \
 && cd / \
 && apk del ${build_packages} \
 && rm -rf /tmp/* \
 && rm -rf /var/cache/apk/*

COPY rsyslog.conf /etc/rsyslog.conf
COPY postfix_virtual /etc/postfix/virtual
COPY run.sh /run.sh
RUN chmod +x /run.sh

USER root

EXPOSE 25
EXPOSE 465
EXPOSE 587
CMD ["/run.sh"]
