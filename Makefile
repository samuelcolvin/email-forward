.DEFAULT_GOAL:=run-local

.PHONY: create-host
create-host:
	docker-machine create \
		--driver amazonec2 \
		--amazonec2-instance-type t2.nano \
		--amazonec2-root-size 8 \
		--amazonec2-iam-instance-profile email-forward-profile \
		email-forward

.PHONY: create-aws-components
create-aws-components:
	@echo "creating role..."
	aws --profile personal iam create-role --role-name email-forward --assume-role-policy-document file://iam-policy/trust.json
	@echo "creating policy..."
	aws --profile personal iam put-role-policy --role-name email-forward --policy-name email-forward-perms --policy-document file://iam-policy/permissions.json
	@echo "creating instance profile..."
	aws --profile personal iam create-instance-profile --instance-profile-name email-forward-profile
	aws --profile personal iam add-role-to-instance-profile --instance-profile-name email-forward-profile --role-name email-forward
	@echo "creating log group..."
	aws --profile personal logs create-log-group --log-group-name EmailForward

.PHONY: build
build: C=$(shell git rev-parse HEAD)
build: BT="$(shell date)"
build: BUILD_ARGS=--build-arg COMMIT=$(C) --build-arg BUILD_TIME=$(BT)
build:
	docker build . -f docker/Dockerfile.base -t email-forward-base -q
	docker build . -t email-forward $(BUILD_ARGS) -q

.PHONY: run-local
build: C=$(shell git rev-parse HEAD)
run-local: build
	docker run -it --rm=true -p=8025:8025 email-forward

.PHONY: deploy
deploy: build
	docker stop email-forward && docker rm email-forward || true
	docker run -d -p=25:25 -p=465:465 -p=587:587 --restart unless-stopped \
		--log-driver=awslogs \
		--log-opt awslogs-region=eu-west-1 \
		--log-opt awslogs-group=EmailForward \
		--log-opt awslogs-stream=email-forward \
		--name email-forward \
		email-forward
