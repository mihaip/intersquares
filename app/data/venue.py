from google.appengine.ext import db

import base.util

DEFAULT_VENUE_ICON = 'https://foursquare.com/img/categories/question.png'

class Venue(db.Model):
  venue_id = db.StringProperty(required=True)
  last_update = db.DateTimeProperty(auto_now=True,indexed=False)

  name = db.StringProperty(indexed=False)
  icon = db.StringProperty(indexed=False)

  city = db.StringProperty(indexed=False)
  state = db.StringProperty(indexed=False)
  country = db.StringProperty(indexed=False)
  lat = db.FloatProperty()
  lng = db.FloatProperty()

  def has_location(self):
    return self.city or self.state or self.country

  def display_location(self):
    def city_state():
      if self.city and self.state:
        return '%s, %s' % (self.city, self.state)
      return self.city or self.state

    if not self.country or self.country == 'USA':
      return city_state()

    return '%s, %s' % (city_state(), self.country)

  def has_location_url(self):
    return self.lat and self.lng

  def location_url(self):
    return 'http://maps.google.com/maps?%s' % base.util.encode_parameters({
          'q': '%g,%g (%s)' % (self.lat, self.lng, self.name)
        })

  @staticmethod
  def create_if_needed(venue_json_data):
    def sanitize(s):
      if not s: return s
      return s.replace('\n', ' ').replace('\r', ' ')

    venue_id = venue_json_data['id']
    existing = Venue.get_by_venue_id(venue_id)
    if existing:
      return existing, False

    venue = Venue(key_name = venue_id, venue_id = venue_id)
    venue.name = sanitize(venue_json_data.get('name', None))
    if venue_json_data.get('categories', []):
      venue.icon = venue_json_data['categories'][0]['icon']
    else:
      venue.icon = DEFAULT_VENUE_ICON

    if 'location' in venue_json_data:
      venue_location_json_data = venue_json_data.get('location', {})
      venue.city = sanitize(venue_location_json_data.get('city', None))
      venue.state = sanitize(venue_location_json_data.get('state', None))
      venue.country = sanitize(venue_location_json_data.get('country', None))
      venue.lat = venue_location_json_data.get('lat', None)
      venue.lng = venue_location_json_data.get('lng', None)

    return venue, True

  @staticmethod
  def get_by_venue_id(venue_id):
    return Venue.get_by_key_name(venue_id)
