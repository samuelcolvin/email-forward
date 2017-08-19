#!/usr/bin/env bash
docker-machine create \
    --driver amazonec2 \
    --amazonec2-instance-type t2.nano \
    --amazonec2-root-size 8 \
    --amazonec2-iam-instance-profile docker-postfix-profile \
    docker-postfix
