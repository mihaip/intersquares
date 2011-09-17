import datetime

from google.appengine.ext import db

import base.util
import data.checkins
import data.session

_MAX_USER_DATA_AGE = datetime.timedelta(days=1)

class CheckinsProperty(base.util.PickledProperty):
  force_type = data.checkins.Checkins

class User(db.Model):
  foursquare_id = db.StringProperty(required=True)
  last_update = db.DateTimeProperty(auto_now=True)

  # User info
  first_name = db.TextProperty()
  last_name = db.TextProperty()
  home_city = db.TextProperty()
  photo_url = db.TextProperty()
  gender = db.TextProperty()
  phone_number = db.TextProperty()
  twitter_username = db.TextProperty()
  facebook_id = db.TextProperty()
  email_address = db.TextProperty()

  checkins = CheckinsProperty()

  def has_checkins(self):
    return self.checkins != None and self.checkins.length()

  def get_oldest_checkin_time(self):
    return self.checkins.oldest().time

  def get_newest_checkin_time(self):
    return self.checkins.newest().time

  def _is_stale(self):
    return datetime.datetime.utcnow() - self.last_update > _MAX_USER_DATA_AGE

  def _update(self, api):
    user_info = api.get('users/self')

    self.first_name = user_info['user'].get('firstName', None)
    self.last_name = user_info['user'].get('lastName', None)
    self.home_city = user_info['user'].get('homeCity', None)
    self.photo_url = user_info['user'].get('photo', None)
    self.gender = user_info['user'].get('gender', None)
    if 'contact' in user_info['user']:
      self.phone_number = user_info['user']['contact'].get('phone', None)
      self.twitter_username = user_info['user']['contact'].get('twitter', None)
      self.facebook_id = user_info['user']['contact'].get('facebook', None)
      self.email_address = user_info['user']['contact'].get('email', None)

  @staticmethod
  def get_by_external_id(external_id):
    session = data.session.Session.get_by_external_id(external_id)
    if not session:
      return None
    return User.all().filter('foursquare_id = ', session.foursquare_id).get()

  @staticmethod
  def get_by_foursquare_id(foursquare_id, api):
    user = User.all().filter('foursquare_id = ', foursquare_id).get()

    if not user:
      user = User._create(foursquare_id, api)
      user.put()
    elif user._is_stale():
      user._update(api)
      user.put()

    return user

  @staticmethod
  def _create(foursquare_id, api):
    user = User(foursquare_id = foursquare_id)
    user._update(api)
    return user
