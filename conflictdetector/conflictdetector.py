#!/usr/bin/env python3
"""Detects time conflicts in Zoom meetings and posts a summary to a webhook.

A meeting conflicts with another meeting if the (start, end) ranges overlap
and if the host is the same user.
"""

import collections
import datetime
import itertools
import logging
import json
import requests
import os
from zoomus import ZoomClient
from dateutil import tz

Meeting = collections.namedtuple('Meeting', ['id', 'title', 'start_time', 'end_time'])

def determine_conflicts(meetings):
  conflicts = []

  meeting_ranges = [
    Meeting(
      meeting['id'],
      meeting['topic'],
      datetime.datetime.strptime(meeting['start_time'], '%Y-%m-%dT%H:%M:%S%z'),
      datetime.datetime.strptime(meeting['start_time'], '%Y-%m-%dT%H:%M:%S%z') + datetime.timedelta(minutes=meeting.get('duration', 90))
    )
    for meeting in meetings
    if 'start_time' in meeting
  ]

  # This is inefficient but the list comes sorted from Zoom and n < 30 in practice.
  for pair in itertools.product(meeting_ranges, repeat=2):
    if pair[0].id < pair[1].id: # Pick a direction since overlapping is commutative
      if max(pair[0].start_time, pair[1].start_time) < min(pair[0].end_time, pair[1].end_time):
        conflicts.append(pair)

  return conflicts


def report_conflict(webhook_url, report_string):
  logging.warning(report_string)

  if webhook_url:
    webhook_data = {'text': report_string}
    response = requests.post(
      webhook_url, data=json.dumps(webhook_data),
      headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
      raise ValueError(
          'Request to webhook returned an error %s, the response is:\n%s'
          % (response.status_code, response.text)
      )


def run(zoom_api_key, zoom_api_secret, webhook_url, timezone):
  timezone = tz.gettz(timezone)
  client = ZoomClient(zoom_api_key, zoom_api_secret)

  user_list_response = client.user.list()
  user_list = json.loads(user_list_response.content)

  for user in user_list['users']:
    user_id = user['id']
    meetings = json.loads(client.meeting.list(user_id=user_id, type='upcoming').content)['meetings']

    conflicts = determine_conflicts(meetings)

    if conflicts:
      for conflict in conflicts:
        report = f'Conflict detected on account {user["email"]}\n'
        (meeting_1, meeting_2) = conflict
        time_format = "%m/%d/%Y, %I:%M:%S %p"
        meeting_1_start = meeting_1.start_time.astimezone(timezone).strftime(time_format)
        meeting_1_end = meeting_1.end_time.astimezone(timezone).strftime(time_format)
        meeting_2_start = meeting_2.start_time.astimezone(timezone).strftime(time_format)
        meeting_2_end = meeting_2.end_time.astimezone(timezone).strftime(time_format)

        report += f'{meeting_1.title}: {meeting_1_start} - {meeting_1_end}\n'
        report += f'{meeting_2.title}: {meeting_2_start} - {meeting_2_end}\n'
        report_conflict(webhook_url, report)
    else:
      logging.info('No upcoming conflicts detected')


def main():
  from dotenv import load_dotenv
  load_dotenv()
  run(
    zoom_api_key=os.getenv('ZOOM_API_KEY'),
    zoom_api_secret=os.getenv('ZOOM_API_SECRET'),
    webhook_url=os.getenv('WEBHOOK_URL'),
    timezone=os.getenv('TIMEZONE'),
  )

if __name__ == '__main__':
  main()
