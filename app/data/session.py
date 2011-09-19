from google.appengine.ext import db

import base.util

def _generate_session_id():
  return base.util.generate_id('s')

def _generate_external_id():
  return base.util.generate_id('e')

class Session(db.Model):
  session_id = db.StringProperty(required=True)
  foursquare_id = db.StringProperty(required=True)
  external_id = db.StringProperty(required=True)
  oauth_token = db.TextProperty(indexed=False)

  def update(self, oauth_token):
    self.session_id = _generate_session_id()
    self.oauth_token = oauth_token

  @staticmethod
  def create(foursquare_id, oauth_token):
    return Session(
        session_id = _generate_session_id(),
        foursquare_id = foursquare_id,
        external_id = _generate_external_id(),
        oauth_token = oauth_token)

  @staticmethod
  def get_by_foursquare_id(foursquare_id):
    return Session.all().filter('foursquare_id = ', foursquare_id).get()

  @staticmethod
  def get_by_session_id(session_id):
    return Session.all().filter('session_id = ', session_id).get()

  @staticmethod
  def get_by_external_id(external_id):
    return Session.all().filter('external_id = ', external_id).get()
