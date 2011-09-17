import Cookie
import os
import urlparse

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import base.api
import data.session
import data.user
import foursquare_config

class BaseHandler(webapp.RequestHandler):
  def _render_template(self, template_file_name, template_values={}):
    template_path = os.path.join(
        os.path.dirname(__file__), '..', 'templates', template_file_name)
    rendered_template = template.render(template_path, template_values)
    # Django templates are returned as utf-8 encoded by default
    if not isinstance(rendered_template, unicode):
      rendered_template = unicode(rendered_template, 'utf-8')
    return rendered_template

  def _write_template(
      self,
      template_file_name,
      template_values={},
      content_type='text/html',
      charset='utf-8'):
    self.response.headers['Content-Type'] = \
        '%s; charset=%s' % (content_type, charset)
    self.response.out.write(
        self._render_template(template_file_name, template_values))

  def _write_error(self, error_code):
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.set_status(error_code)

  def _write_not_found(self):
    self._write_error(404)

  def _write_input_error(self, error_message):
    self._write_error(400)
    self.response.out.write('Input error: %s' % error_message)

class SessionHandler(BaseHandler):
  SESSION_COOKIE_NAME = 'sid'

  def _has_request_session(self):
    return self.SESSION_COOKIE_NAME in self.request.cookies

  def _get_session_from_request(self):
    return data.session.Session.get_by_session_id(
        self.request.cookies[self.SESSION_COOKIE_NAME])

  def _set_request_session(self, session):
    cookie = Cookie.SimpleCookie()
    cookie[self.SESSION_COOKIE_NAME] = session.session_id
    morsel = cookie[self.SESSION_COOKIE_NAME]
    morsel['path'] = '/'
    # TODO(mihaip): expiration?

    self.response.headers.add_header(
        'Set-Cookie', morsel.output(header='').lstrip())

  def _remove_request_session(self):
    cookie = Cookie.SimpleCookie()
    cookie[self.SESSION_COOKIE_NAME] = 'expired'
    morsel = cookie[self.SESSION_COOKIE_NAME]
    morsel['path'] = '/'
    morsel['expires'] = 'Sat, 1-Jan-2000 00:00:00'

    self.response.headers.add_header(
        'Set-Cookie', morsel.output(header='').lstrip())

class FoursquareOAuthHandler(SessionHandler):
  def foursquare_config(self):
    hostname = urlparse.urlparse(self.request.url).hostname
    return foursquare_config.from_hostname(hostname)

class ApiHandler(FoursquareOAuthHandler):
  def get(self):
    if self._has_request_session():
      session = self._get_session_from_request()

      if session:
        self._session = session
        self._api = base.api.Api(session.oauth_token)
        self._get_signed_in()
        return
      else:
        self._remove_request_session()

    self._get_signed_out()

  def _get_signed_in(self):
    raise NotImplementedError()

  def _get_signed_out(self):
    self.redirect('/')

  # convenience methods
  def _get_user(self):
    return data.user.User.get_by_foursquare_id(
        self._session.foursquare_id, self._api)
