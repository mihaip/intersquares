import datetime
import logging

import pytz

import base.util

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

      venue_location_json_data = venue_json_data.get('location', {})
      self.venue_city = venue_location_json_data.get('city', None)
      self.venue_state = venue_location_json_data.get('state', None)
      self.venue_country = venue_location_json_data.get('country', None)
      self.venue_lat = venue_location_json_data.get('lat', None)
      self.venue_lng = venue_location_json_data.get('lng', None)
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

  def has_venue_location(self):
    return self.venue_city or self.venue_state or self.venue_country

  def display_venue_location(self):
    def city_state():
      if self.venue_city and self.venue_state:
        return '%s, %s' % (self.venue_city, self.venue_state)
      return self.venue_city or self.venue_state

    if not self.venue_country or self.venue_country == 'USA':
      return city_state()

    return '%s, %s' % (city_state(), self.venue_country)

  def has_venue_location_url(self):
    return self.venue_lat and self.venue_lng

  def venue_location_url(self):
    return 'http://maps.google.com/maps?%s' % base.util.encode_parameters({
          'q': '%g,%g (%s)' % (self.venue_lat, self.venue_lng, self.venue_name)
        })
