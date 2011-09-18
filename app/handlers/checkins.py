import logging
import urllib

from google.appengine.api import taskqueue

import base.handlers
import data.checkins
import data.user

class UpdateCheckinsHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    user = self._get_user()

    if user.needs_checkin_update():
      if not user.checkins:
        user.checkins = data.checkins.Checkins()
      direction = user.checkins.length() and 'forward' or 'backward'
      user.is_updating = True
      user.put()

      taskqueue.add(
          queue_name='update-checkins',
          url='/tasks/checkins/update',
          params={
            'oauth_token': self._session.oauth_token,
            'foursquare_id': user.foursquare_id,
            'direction': direction
          })

    self.response.out.write('OK')

class UpdateCheckinsTaskHandler(base.handlers.BaseHandler):
  def post(self):
    oauth_token = self.request.get('oauth_token')
    api = base.api.Api(oauth_token)
    user = data.user.User.get_by_foursquare_id(
        self.request.get('foursquare_id'), api)
    direction = self.request.get('direction')

    if direction == 'forward':
      has_more = user.checkins.fetch_newer(api)
    else:
      has_more = user.checkins.fetch_older(api)

    if not has_more:
      user.is_updating = False

    user.put()

    if has_more:
      taskqueue.add(
          queue_name='update-checkins',
          url='/tasks/checkins/update',
          params={
            'oauth_token': oauth_token,
            'foursquare_id': user.foursquare_id,
            'direction': direction
          })

    self.response.out.write('OK')

class UpdateCheckinsStateHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    user = self._get_user()

    return self._write_json({
      'is_updating': user.is_updating or False,
      'checkin_count': user.checkins and user.checkins.length() or 0,
    })

class ClearCheckinsHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    user = self._get_user()
    user.checkins = data.checkins.Checkins()
    user.put()
    self.redirect('/')

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

    # TODO(mihaip): switch to initiating update and showing progress client-side
    if not this_user.checkins:
      this_user.checkins = data.checkins.Checkins()

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

class QrCodeIntersectHandler(base.handlers.BaseHandler):
  def get(self, external_id):
    qr_code_url = \
        'https://chart.googleapis.com/chart?chs=320x320&cht=qr&chl=%s' % (
        urllib.quote(self._generate_absolute_url('i/' + external_id)))
    self._write_template(
        'intersections-qr-code.html', {
            'qr_code_url': qr_code_url,
        })
