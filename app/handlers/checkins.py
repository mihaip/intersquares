import base.handlers
import data.checkins

class UpdateCheckinsHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    user = self._get_user()
    if not user.checkins:
      user.checkins = data.checkins.Checkins()
    user.checkins.update(self._api)
    user.put()

    self.redirect('/')

class ClearCheckinsHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    pass

