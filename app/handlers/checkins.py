import base.handlers
import data.checkins
import data.user

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

class IntersectCheckinsHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    this_user = self._get_user()

    other_user_external_id = self.request.get('external_id').strip()
    if not other_user_external_id:
        self._write_input_error('Missing "external_id" parameter')
        return

    other_user = data.user.User.get_by_external_id(other_user_external_id)
    if not other_user:
        self._write_input_error('Unknown user "%s"' % other_user_external_id)
        return

    intersection = this_user.checkins.intersection(other_user.checkins)
    intersection.reverse()

    self._write_template(
        'intersections.html', {
            'this_user': this_user,
            'other_user': other_user,
            'intersection': intersection,
        })
