from .conflictdetector import run
import dotenv
import os

def handle(req):
  config = dotenv.dotenv_values("/var/openfaas/secrets/conflictdetector-keys")
  run(
    zoom_api_key=config['ZOOM_API_KEY'],
    zoom_api_secret=config['ZOOM_API_SECRET'],
    webhook_url=config['WEBHOOK_URL'],
  )
  return '{"status":"ok"}'
