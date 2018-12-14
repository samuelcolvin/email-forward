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
build: C=$(shell git rev-parse HEAD)
build: BT="$(shell date)"
build: BUILD_ARGS=--build-arg COMMIT=$(C) --build-arg BUILD_TIME=$(BT)
build:
	docker build src/ -f src/Dockerfile.base -t email-forward-base
	docker build src/ -t samuelcolvin/email-forward $(BUILD_ARGS)

.PHONY: run-local
build: C=$(shell git rev-parse HEAD)
run-local: build
	docker run -it --rm=true -p=8025:25 email-forward

.PHONY: push
push: build
	docker push samuelcolvin/email-forward

.PHONY: deploy
deploy: COMMIT=$(shell git rev-parse HEAD)-$(shell date +%Y-%m-%dT%Hh%Mm%Ss)
deploy:
	docker pull samuelcolvin/email-forward:latest
	docker stop email-forward && docker rm email-forward || true
	docker run -d -p=25:25 -p=465:465 -p=587:587 --restart unless-stopped \
		-e "HOST_NAME=$(HOST_NAME)" \
		-e "FORWARD_TO=$(FORWARD_TO)" \
		-e "FORWARD_PASSWORD=$(FORWARD_PASSWORD)" \
		-e "FORWARDED_DOMAINS=$(FORWARDED_DOMAINS)" \
		-e "SENTRY_DSN=$(SENTRY_DSN)" \
		--log-driver=awslogs \
		--log-opt awslogs-region=eu-west-1 \
		--log-opt awslogs-group=EmailForward \
		--log-opt awslogs-stream="email-forward-$(COMMIT)" \
		--name email-forward \
		samuelcolvin/email-forward
