.DEFAULT_GOAL:=run-local

.PHONY: aws-whoami
aws-whoami:
	aws iam get-user

.PHONY: create-aws-components
create-aws-components: aws-whoami
	# creating role...
	aws iam create-role --role-name email-forward --assume-role-policy-document file://iam-policy/trust.json
	# creating policy...
	aws iam put-role-policy --role-name email-forward --policy-name email-forward-perms --policy-document file://iam-policy/permissions.json
	# creating instance profile...
	aws iam create-instance-profile --instance-profile-name email-forward-profile
	aws iam add-role-to-instance-profile --instance-profile-name email-forward-profile --role-name email-forward
	# creating log group...
	aws logs create-log-group --log-group-name EmailForward

.PHONY: create-host
create-host: aws-whoami
	@echo "region: $(AWS_DEFAULT_REGION)"
	docker-machine create \
		--driver amazonec2 \
		--amazonec2-zone b \
		--amazonec2-instance-type t2.nano \
		--amazonec2-root-size 8 \
		--amazonec2-iam-instance-profile email-forward-profile \
		email-forward

.PHONY: build
build: COMMIT=$(shell git rev-parse --short HEAD)-$(shell date +%Y-%m-%dT%Hh%Mm%Ss)
build:
	@rm -r src/email_forward/__pycache__ || true
	docker build src/ -f src/Dockerfile.base -t email-forward-base
	docker build src/ -t samuelcolvin/email-forward --build-arg COMMIT=$(COMMIT)

.PHONY: run-local
run-local: SSL_CRT=$(shell cat ssl.crt | base64)
run-local: SSL_KEY=$(shell cat ssl.key | base64)
run-local: build
	@echo "docker run -p=8025:8025 ... samuelcolvin/email-forward"
	@docker run \
	-it \
	--rm=true \
	-p=8025:8025 \
	-e "SSL_CRT=$(SSL_CRT)" \
	-e "SSL_KEY=$(SSL_KEY)" \
	-e "FORWARD_TO=$(FORWARD_TO)" \
	-e "FORWARDED_DOMAINS=$(FORWARDED_DOMAINS)" \
	--name email-forward-test \
	samuelcolvin/email-forward

.PHONY: push
push: build
	docker push samuelcolvin/email-forward

.PHONY: push-deploy
push-deploy: push
	./deploy.sh
