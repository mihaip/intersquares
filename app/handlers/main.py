import base.handlers

class IndexHandler(base.handlers.BaseHandler):
  def get(self):
    self._write_template('index-signed-out.html')
