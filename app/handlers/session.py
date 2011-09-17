from google.appengine.api import urlfetch
from django.utils import simplejson

import base.handlers
import data.session

class FoursquareConnectHandler(base.handlers.FoursquareOAuthHandler):
  def get(self):
    config = self.foursquare_config()
    self.redirect(
        'https://foursquare.com/oauth2/authenticate?' +
            'client_id=%s&response_type=code&redirect_uri=%s' %
        (config.client_id, config.callback_url))

class FoursquareCallbackHandler(base.handlers.FoursquareOAuthHandler):
  def get(self):
    code = self.request.get('code')
    config = self.foursquare_config()
    url = ('https://foursquare.com/oauth2/access_token?' +
        'client_id=%s&client_secret=%s&grant_type=authorization_code&' +
        'redirect_uri=%s&code=%s') % (
        config.client_id, config.client_secret, config.callback_url, code)
    auth_json = urlfetch.fetch(url)
    oauth_token = simplejson.loads(auth_json.content)['access_token']

    user_info_url = ('https://api.foursquare.com/v2/users/self?' +
        'oauth_token=%s' % oauth_token)
    user_info_json = urlfetch.fetch(user_info_url)
    user_info = simplejson.loads(user_info_json.content)

    foursquare_id = user_info['response']['user']['id']

    session = data.session.Session.get_by_foursquare_id(foursquare_id)
    if session:
      session.update(oauth_token)
    else:
      session = data.session.Session.create(foursquare_id, oauth_token)
    session.put()

    self._set_request_session(session)

    self.redirect('/')

class SignOutHandler(base.handlers.SessionHandler):
  def get(self):
    # TODO(mihaip): should we remove the Foursquare session too? Otherwise
    # since we use /authenticate, it's hard to switch users on the fly.
    self._remove_request_session()
    self.redirect('/')
