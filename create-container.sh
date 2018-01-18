#!/usr/bin/env bash
if [ -z "$MY_DOMAIN" ] || [ -z "$FORWARD_TO" ] || [ -z "$FORWARDED_DOMAINS" ]; then
    echo "\$MY_DOMAIN, \$FORWARD_TO and \$FORWARDED_DOMAINS are required but one or more are empty or unset"
    exit 1
fi

docker pull samuelcolvin/postfix-forward:latest
docker run -d -p=25:25 -p=465:465 -p=587:587 --restart unless-stopped \
    -e "MY_DOMAIN=$MY_DOMAIN" -e "FORWARD_TO=$FORWARD_TO" -e "FORWARDED_DOMAINS=$FORWARDED_DOMAINS" \
    --log-driver=awslogs \
    --log-opt awslogs-region=$AWS_DEFAULT_REGION \
    --log-opt awslogs-group=DockerPostfix \
    --log-opt awslogs-stream=docker-postfix \
    --name postfix \
    samuelcolvin/postfix-forward
