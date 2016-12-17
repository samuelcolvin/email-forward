# docker-postfix-forward

email forwarding with a tiny alpine linux docker image running postfix.

## Settings

Copy `env.sh.template` to `env.sh` and configure the settings.

To "activate" those settings run `eval $(cat env.sh)`.

## Testing

To build

    docker build -t postfix-forward .

To run locally (with environment variables set):

    ./run-local.sh

You can then test by calling `eval $(cat env.sh); ./test.py local` in another terminal.

## Deploying

Roughly run

    eval $(cat env.sh)
    ./create-iam-policy-logs.sh
    ./create-host.sh
    eval $(docker-machine env docker-postfix)
    ./create-container.sh

Log into AWS, then:
* go to ec2 > "Security Groups" and add ports 25, 465, 587 to the "docker-machine" secuity group.
* go to ec2 > "Elastic IPs", allocate a new ip and associate it with the "docker-postfix" instance.

You'll need to run `docker-machine regenerate-certs docker-postfix` once you assign the new ip.

You should then be able to test with

    ./test.py
