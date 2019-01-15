#!/usr/bin/env bash
. ~/.bashrc
. env/bin/activate

export AWS_DEFAULT_REGION='...'
export AWS_BUCKET_NAME='...'
export AWS_ACCESS_KEY_ID='...'
export AWS_SECRET_ACCESS_KEY='...'
export HOST_NAME='...'
export FORWARD_TO='...'
export FORWARDED_DOMAINS='...'
export SENTRY_DSN='...'

export PS1="EMAIL-FORWARD $PS1"
