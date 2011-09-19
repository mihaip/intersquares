import logging
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
        'https://foursquare.com/oauth2/authorize?' +
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
    try:
      oauth_token = simplejson.loads(auth_json.content)['access_token']
    except simplejson.JSONDecodeError, err:
      logging.exception(err)
      logging.error('JSON error: %s', str(err))
      logging.error('Request URL: %s',  url)
      logging.error('Foursquare response content: %s', auth_json.content)
      logging.error('Response status code: %d', auth_json.status_code)
      logging.error('Response headers: %s', str(auth_json.headers))

      self._write_error(500)
      self.response.out.write(
          'Got a %d status code from Foursquare. It might go away if you ' +
          'refresh this page\n' % auth_json.status_code)
      return
    except KeyError, err:
      logging.exception(err)
      logging.error('KeyError: %s', str(err))
      logging.error('Request URL: %s',  url)
      logging.error('Foursquare response content: %s', auth_json.content)
      logging.error('Response status code: %d', auth_json.status_code)
      logging.error('Response headers: %s', str(auth_json.headers))
      logging.error(
          'Response JSON: %s', str(simplejson.loads(auth_json.content)))

      self._write_error(500)
      self.response.out.write(
          'Oops, couldn\'t get what we need from Foursquare\'s JSON response. ' +
          'Things might be better if you refresh this page\n')
      return


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
    self._remove_request_session()
    self.redirect('/')
