# docker-postfix-forward

email forwarding with a tiny alpine linux docker image running postfix


To build

    docker build -t postfix-forward .

To run locally

    docker run -t -i --rm=true -p=8587:587 postfix-forward


You can then test with `python3 test.py`
