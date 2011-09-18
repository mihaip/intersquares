import urllib

from google.appengine.api import urlfetch
from django.utils import simplejson

import base.handlers
import data.session

class FoursquareConnectHandler(base.handlers.FoursquareOAuthHandler):
  def get(self):
    config = self.foursquare_config()

    callback_url = config.callback_url
    if self.request.get('continue'):
      callback_url += '?continue=' + urllib.quote(self.request.get('continue'))

    self.redirect(
        'https://foursquare.com/oauth2/authenticate?' +
            base.util.encode_parameters({
              'client_id': config.client_id,
              'response_type': 'code',
              'redirect_uri': callback_url
            }))

class FoursquareCallbackHandler(base.handlers.FoursquareOAuthHandler):
  def get(self):
    code = self.request.get('code')
    config = self.foursquare_config()
    url = ('https://foursquare.com/oauth2/access_token?' +
        'client_id=%s&client_secret=%s&grant_type=authorization_code&' +
        'redirect_uri=%s&code=%s') % (
        config.client_id, config.client_secret, config.callback_url, code)
    auth_json = urlfetch.fetch(url, deadline=10)
    oauth_token = simplejson.loads(auth_json.content)['access_token']

    user_info_url = ('https://api.foursquare.com/v2/users/self?' +
        'oauth_token=%s' % oauth_token)
    user_info_json = urlfetch.fetch(user_info_url, deadline=10)
    user_info = simplejson.loads(user_info_json.content)

    foursquare_id = user_info['response']['user']['id']

    session = data.session.Session.get_by_foursquare_id(foursquare_id)
    if session:
      session.update(oauth_token)
    else:
      session = data.session.Session.create(foursquare_id, oauth_token)
    session.put()

    self._set_request_session(session)

    if self.request.get('continue'):
      # TODO(mihaip): check that the continue URL belongs to us
      self.redirect(self.request.get('continue'))
    else:
      self.redirect('/')

class SignOutHandler(base.handlers.SessionHandler):
  def get(self):
    # TODO(mihaip): should we remove the Foursquare session too? Otherwise
    # since we use /authenticate, it's hard to switch users on the fly.
    self._remove_request_session()
    self.redirect('/')
