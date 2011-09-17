from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import handlers.main
import handlers.session

def main():
  application = webapp.WSGIApplication([
          # main
          ('/', handlers.main.IndexHandler),

          # session
          ('/4sq/connect', handlers.session.FoursquareConnectHandler),
          ('/4sq/callback', handlers.session.FoursquareCallbackHandler),
          ('/sign-out', handlers.session.SignOutHandler),
      ],
      debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
