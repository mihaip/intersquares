import os
import sys

sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'third_party'))

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import handlers.checkins

def main():
  application = webapp.WSGIApplication([
          ('/tasks/checkins/update', handlers.checkins.UpdateCheckinsTaskHandler),
      ],
      debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
