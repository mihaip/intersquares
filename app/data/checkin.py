import datetime

import pytz

DEFAULT_VENUE_ICON = 'https://foursquare.com/img/categories/question.png'

class Checkin(object):
  def __init__(self, json_data):
    self.id = json_data['id']
    self.type = json_data['type']
    self.private = 'private' in json_data
    self.timezone = json_data.get('timeZone', None)
    if 'venue' in json_data:
      venue_json_data = json_data['venue']
      self.venue_id = venue_json_data['id']
      self.venue_name = venue_json_data.get('name', None)
      if venue_json_data.get('categories', []):
        self.venue_icon = venue_json_data['categories'][0]['icon']
      else:
        self.venue_icon = DEFAULT_VENUE_ICON
    else:
      self.venue_id = None
      # Other fields shouldn't matter, since should_use() will make us skip
      # this checkin.
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

