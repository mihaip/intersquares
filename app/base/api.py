import logging

from django.utils import simplejson
from google.appengine.api import urlfetch

import base.util

class ApiException(Exception):
    pass

class Api(object):
  def __init__(self, oauth_token):
    self._oauth_token = oauth_token

  def get(self, path, parameters={}):
    logging.info('API request: %s' % path)

    request_url = ('https://api.foursquare.com/v2/%s?' +
        'oauth_token=%s&%s') % (path, self._oauth_token,
            base.util.encode_parameters(parameters))
    response = urlfetch.fetch(request_url, deadline=10)
    response_json = simplejson.loads(response.content)
    if response_json['meta']['code'] == 200:
      return response_json['response']
    else:
      raise ApiException(response_json['meta'])

