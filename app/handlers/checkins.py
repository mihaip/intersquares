import urllib

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
  def _get_other_user(self):
    other_user_external_id = self.request.get('external_id').strip()
    if not other_user_external_id:
        self._write_input_error('Missing "external_id" parameter')
        return None

    other_user = data.user.User.get_by_external_id(other_user_external_id)
    if not other_user:
        self._write_input_error('Unknown user "%s"' % other_user_external_id)
        return None

    return other_user

  def _get_signed_in(self):
    this_user = self._get_user()
    other_user = self._get_other_user()
    if not other_user:
      return

    # TODO(mihaip): show progress?
    if not this_user.checkins:
      this_user.checkins = data.checkins.Checkins()
    if not this_user.checkins.length():
      this_user.checkins.update(self._api)
      this_user.put()

    intersection = this_user.checkins.intersection(other_user.checkins)
    intersection.reverse()

    self._write_template(
        'intersections-signed-in.html', {
            'this_user': this_user,
            'other_user': other_user,
            'intersection': intersection,
        })

  def _get_signed_out(self):
    other_user = self._get_other_user()
    if not other_user:
      return

    connect_url = '/4sq/connect?continue=%s' % urllib.quote(self.request.url)

    self._write_template(
        'intersections-signed-out.html', {
            'other_user': other_user,
            'connect_url': connect_url,
        })


class ShortIntersectHandler(base.handlers.BaseHandler):
  def get(self, external_id):
    self.redirect(
        '/checkins/intersect?external_id=%s' % urllib.quote(external_id))
