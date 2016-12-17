# docker-postfix-forward

Email forwarding with a tiny alpine linux docker image running postfix.

Logs are sent to CloudWatch using dockers log drivers so you have a record of email activity.
 
I use this image to forward emails from domains I own to my gmail inbox, running on a t2.nano instance it 
costs $4.60/mo all in.

## Settings

Copy `env.sh.template` to `env.sh` and configure the settings.

To "activate" those settings run `eval $(cat env.sh)`.

## Testing

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

Set up your DNS to point to `mail.<mydomain>` where `<mydomain>` is the domain you set in `env.sh`.

You should then be able to test with

    ./test.py

## Building

(This isn't generally necessary as the docker image is available at 
[samuelcolvin/postfix-forward](https://hub.docker.com/r/samuelcolvin/postfix-forward/)).

    docker build -t postfix-forward .
