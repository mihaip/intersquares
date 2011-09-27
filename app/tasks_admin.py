import os
import sys

from google.appengine.dist import use_library
use_library('django', '1.2')

sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'third_party'))

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import handlers.checkins

def main():
  application = webapp.WSGIApplication([
          ('/admin/checkins/reload', handlers.checkins.ReloadCheckinsAdminHandler),
          ('/tasks/checkins/clear', handlers.checkins.ClearCheckinsTaskHandler),
          ('/tasks/checkins/update', handlers.checkins.UpdateCheckinsTaskHandler),
      ],
      debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
