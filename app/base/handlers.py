import os
import urlparse

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

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

class FoursquareOAuthHandler(BaseHandler):
  def foursquare_config(self):
    hostname = urlparse.urlparse(self.request.url).hostname
    return foursquare_config.from_hostname(hostname)

