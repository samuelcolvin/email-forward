# docker-postfix-forward

email forwarding with a tiny alpine linux docker image running postfix

# Testing

To build

    docker build -t postfix-forward .

To run locally

    docker run -t -i --rm=true -p=8025:25 postfix-forward
    
Modify then run the test script

    ./test.py


You can then test with `./test.py`

# Deploying

Roughly run

    export AWS_ACCESS_KEY_ID="<your aws access key>"
    export AWS_SECRET_ACCESS_KEY="<your aws secret key>"
    export AWS_DEFAULT_REGION=eu-west=1
    ./create-iam-policy-logs.sh
    ./create-host.sh
    eval $(docker-machine env docker-postfix)
    ./create-container.sh

See those files for more details.
