# conflictdetector for Zoom and Slack
When sharing Zoom accounts, sometimes people will accidentally book overlapping
meetings. This script will find and report them to a Slack-style webhook.

## Setup
### Run once without OpenFAAS
* [Get your Zoom API key and secret](https://devforum.zoom.us/t/finding-your-api-key-secret-credentials-in-marketplace/3471)
* [Create an incoming webhook in Slack](https://api.slack.com/messaging/webhooks)
* Copy `.env.example` to `.env` and edit it.
* `python conflictdetector/conflictdetector`

### Run automatically in OpenFAAS and Kubernetes
Assuming you have `faas-cli` and `kubectl` configured and working.
* `faas-cli secret create conflictdetector-keys --from-file=.env`
* `faas-cli deploy -f conflictdetector.yml`

### Build your own image
* Edit `conflictdetector.yml` and update the `image` field to your container registry.
* `faas-cli publish -f conflictdetector.yml --platforms linux/arm/v7,linux/amd64`
* `faas-cli deploy -f conflictdetector.yml`
