from google.appengine.api import urlfetch
from django.utils import simplejson

import base.handlers

class IndexHandler(base.handlers.FoursquareOAuthHandler):
  def get(self):
    if self._has_request_session():
      # TODO(mihaip): handle missing sessions
      session = self._get_session_from_request()

      # TODO(mihaip): foursquare API error handling
      user_info_url = ('https://api.foursquare.com/v2/users/self?' +
          'oauth_token=%s' % session.oauth_token)
      user_info_json = urlfetch.fetch(user_info_url)
      user_info = simplejson.loads(user_info_json.content)

      self._write_template(
          'index-signed-in.html', {
              'user_info': simplejson.dumps(user_info, indent='  '),
          })
    else:
      self._write_template('index-signed-out.html')
