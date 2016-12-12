# docker-postfix-forward

email forwarding with a tiny alpine linux docker image running postfix

# Testing

To build

    docker build -t postfix-forward .

To run locally

    docker run -t -i --rm=true -p=8587:587 postfix-forward


You can then test with `python3 test.py`

# Deploying

Roughly run

    ./create-iam-policy-logs.sh
    ./create-host.sh
    eval $(docker-machine env docker-postfix)
    ./create-container.sh

See those files for more details.
