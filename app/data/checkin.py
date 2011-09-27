import datetime
import logging

from django.utils import simplejson
import pytz

class Checkin(object):
  def __init__(self, json_data):
    self.id = json_data['id']
    self.type = json_data['type']
    self.private = 'private' in json_data
    self.timezone = json_data.get('timeZone', None)
    if 'venue' in json_data:
      venue_json_data = json_data['venue']
      self.venue_id = venue_json_data['id']
    else:
      self.venue_id = None
    self.timestamp = datetime.datetime.fromtimestamp(
        json_data['createdAt'], pytz.UTC)

    # TODO(mihaip): shout, comments, photos, overlaps

  def should_use(self):
    return self.type == 'checkin' and not self.private and self.venue_id

  def get_local_timestamp(self):
    if self.timezone:
      tzinfo = pytz.timezone(self.timezone)
      if tzinfo:
        return self.timestamp.astimezone(tzinfo)
    return self.timestamp

  def display_year(self):
    return self.get_local_timestamp().strftime('%Y')

  def display_date(self):
    return self.get_local_timestamp().strftime('%B %-d, %Y')

  def display_short_date(self):
    return self.get_local_timestamp().strftime('%B %-d')

  def display_time(self):
    return self.get_local_timestamp().strftime('%-H:%M')

  def __str__(self):
    return simplejson.dumps({
      'id': self.id,
      'type': self.type,
      'private': self.private,
      'venue_id': self.venue_id,
      'timestamp': str(self.timestamp),
    }, indent=2)

