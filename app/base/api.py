import logging

from django.utils import simplejson
from google.appengine.api import urlfetch

class ApiException(Exception):
    pass

class Api(object):
  def __init__(self, oauth_token):
    self._oauth_token = oauth_token

  def get(self, path):
    logging.info('API request: %s' % path)

    request_url = ('https://api.foursquare.com/v2/%s?' +
        'oauth_token=%s') % (path, self._oauth_token)
    response = urlfetch.fetch(request_url)
    response_json = simplejson.loads(response.content)
    if response_json['meta']['code'] == 200:
      return response_json['response']
    else:
      raise ApiException(response_json['meta'])

