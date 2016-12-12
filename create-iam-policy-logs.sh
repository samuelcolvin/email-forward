#!/usr/bin/env bash
echo "creating role..."
aws --profile personal iam create-role --role-name docker-postfix --assume-role-policy-document file://iam-policy/trust.json
echo "creating policy..."
aws --profile personal iam put-role-policy --role-name docker-postfix --policy-name docker-postfix-perms --policy-document file://iam-policy/permissions.json
echo "creating instance profile..."
aws --profile personal iam create-instance-profile --instance-profile-name docker-postfix-profile
aws --profile personal iam add-role-to-instance-profile --instance-profile-name docker-postfix-profile --role-name docker-postfix
echo "creating log group..."
aws --profile personal logs create-log-group --log-group-name DockerPostfix
