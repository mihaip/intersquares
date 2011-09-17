import base.handlers

class IndexHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    user = self._get_user()

    self._write_template(
        'index-signed-in.html', {
            'user': user,
        })

  def _get_signed_out(self):
    self._write_template('index-signed-out.html')
