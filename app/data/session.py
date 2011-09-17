from google.appengine.ext import db

import base.util

class Session(db.Model):
  session_id = db.StringProperty(required=True)
  foursquare_id = db.StringProperty(required=True)
  oauth_token = db.TextProperty()

  @staticmethod
  def generate_session_id():
    return base.util.generate_id('s')

  @staticmethod
  def get_by_foursquare_id(foursquare_id):
    return Session.all().filter('foursquare_id = ', foursquare_id).get()

  @staticmethod
  def get_by_session_id(session_id):
    return Session.all().filter('session_id = ', session_id).get()

