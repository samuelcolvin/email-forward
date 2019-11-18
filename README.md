# email-forward

Email forwarding with a tiny alpine linux docker image running a python SMTP proxy server.

All emails are saved to S3 even if forwarding fails.

Logs are sent to CloudWatch using dockers log drivers so you have a record of email activity.
 
I use this image to forward emails from domains I own to my gmail inbox, running on a t2.nano instance it 
costs $4.60/mo all in.

## Usage

To build, push and deploy in one (assuming you're me):

    make push-deploy

To just deploy use `./deploy.sh`.
