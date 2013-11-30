import logging

from django.utils import simplejson
from google.appengine.api import urlfetch

import base.util

_FOURSQUARE_API_VERSION = '20131130'

class ApiException(Exception):
    pass

class Api(object):
  def __init__(self, oauth_token):
    self._oauth_token = oauth_token

  def get(self, path, parameters={}):
    request_url = ('https://api.foursquare.com/v2/%s?' +
        'oauth_token=%s&v=%s&%s') % (path, self._oauth_token,
            _FOURSQUARE_API_VERSION, base.util.encode_parameters(parameters))
    logging.info('API request: %s' % request_url)

    response = urlfetch.fetch(request_url, deadline=60)
    response_json = simplejson.loads(response.content)
    if response_json['meta']['code'] == 200:
      response_meta = response_json['meta']
      if 'errorType' in response_meta:
        logging.warning(
            'API request successful, but also got error "%s" (details: "%s").',
            response_meta['errorType'], response_meta.get('errorDetail'))
      return response_json['response']
    else:
      raise ApiException(response_json['meta'])

