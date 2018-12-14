#!/usr/bin/env bash
. ~/.bashrc
. env/bin/activate

export AWS_DEFAULT_REGION="eu-west-1"
export AWS_ACCESS_KEY_ID="<aws access key>"
export AWS_SECRET_ACCESS_KEY="<aws secret key>"
export HOST_NAME="<domain to use as 'mydomain' in postfix>"
export FORWARD_TO="<the email address to forward all emails to>"
export FORWARDED_DOMAINS="<space seperated list of domains to forward emails for>"
export SENTRY_DSN="<sentry dsn>"

export PS1="EMAIL-FORWARD $PS1"
