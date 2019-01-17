#!/usr/bin/env bash
set -e
eval $(docker-machine env email-forward)

VERSION="`git rev-parse --short HEAD`-`date +%Y-%m-%dT%Hh%Mm%Ss`"
docker pull samuelcolvin/email-forward:latest
docker ps
echo "stopping existing container..."
docker stop email-forward && docker rm email-forward || true
echo "starting docker image, version: $VERSION"
docker run -d \
  -p=25:8025 \
  --restart unless-stopped \
  -e "FORWARD_TO=$FORWARD_TO" \
  -e "FORWARDED_DOMAINS=$FORWARDED_DOMAINS" \
  -e "SENTRY_DSN=$SENTRY_DSN" \
  -e "SSL_CRT=`cat ssl.crt | base64`" \
  -e "SSL_KEY=`cat ssl.key | base64`" \
  -e "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION" \
  -e "AWS_BUCKET_NAME=$AWS_BUCKET_NAME" \
  -e "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" \
  -e "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" \
  --log-driver=awslogs \
  --log-opt awslogs-region=eu-west-1 \
  --log-opt awslogs-group=EmailForward \
  --log-opt awslogs-stream="email-forward-$VERSION" \
  --name email-forward \
  samuelcolvin/email-forward

echo "docker image started, waiting for container to come up..."
sleep 5
docker ps
