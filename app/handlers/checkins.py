import logging
import urllib

from google.appengine.api import mail
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.runtime import apiproxy_errors

import base.handlers
import data.checkins
import data.intersection
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

    try:
      user.put()
    except (db.BadRequestError, apiproxy_errors.RequestTooLargeError), err:
      logging.exception(err)
      logging.error(
          '%s has too many checkins (%d), dropping some',
          user.foursquare_id, user.checkins.length())
      user.checkins.drop_old_checkins()
      logging.error(
          '%s now has %d checkins',
          user.foursquare_id, user.checkins.length())
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
    self.response.out.write('OK')

class BaseIntersectHandler(base.handlers.ApiHandler):
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

class IntersectCheckinsHandler(BaseIntersectHandler):
  def _get_signed_in(self):
    this_user = self._get_user()
    other_user = self._get_other_user()
    if not other_user:
      return

    self._write_template(
        'intersections-signed-in.html', {
            'this_user': this_user,
            'other_user': other_user,
            'other_user_external_id': self.request.get('external_id').strip(),
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

class IntersectCheckinsDataHandler(BaseIntersectHandler):
  def _get_signed_in(self):
    this_user = self._get_user()
    other_user = self._get_other_user()
    if not other_user:
      return

    short_url = self._generate_absolute_url('i/' + self._session.external_id)
    tweet_text = 'Use Fourquare? See where we would have met: %s' % short_url

    if other_user.foursquare_id == this_user.foursquare_id:
      mihai_user = data.user.User.get_by_foursquare_id('2118', None)
      if mihai_user:
        mihai_session = data.session.Session.get_by_foursquare_id('2118')
        mihai_short_url = self._generate_absolute_url('i/' + mihai_session.external_id)
      else:
        mihai_short_url = None
      self._write_template(
          'intersections-self.snippet', {
              'this_user': this_user,
              'short_url': short_url,
              'tweet_text': tweet_text,
              'mihai_user': mihai_user,
              'mihai_short_url': mihai_short_url,
          })
      return

    intersection_data = this_user.checkins.intersection(other_user.checkins)
    intersection_data.reverse()

    intersection = data.intersection.Intersection.create_or_update(
        base_foursquare_id = this_user.foursquare_id,
        base_external_id = self._session.external_id,
        search_foursquare_id = other_user.foursquare_id,
        search_external_id = self.request.get('external_id').strip(),
        match_count = len(intersection_data))

    if intersection_data and not other_user.doesnt_want_mail and \
        other_user.email_address and not intersection.emailed:
      logging.info('Sending mail')
      self._send_intersection_mail(
          this_user, short_url, other_user, intersection_data)
      intersection.emailed = True
    else:
      logging.info('Not sending mail')
    intersection.put()

    if not intersection_data:
      self._write_template(
          'intersections-empty.snippet', {
            'this_user': this_user,
            'other_user': other_user,
            'short_url': short_url,
            'tweet_text': tweet_text,
          })
      return

    self._write_template(
        'intersections-data.snippet', {
            'this_user': this_user,
            'other_user': other_user,
            'intersection': intersection_data,
            'short_url': short_url,
            'tweet_text': tweet_text,
        })

  def _send_intersection_mail(
      self, this_user, this_user_short_url, other_user, intersection_data):
    message_data = {
      'other_user_display_name': other_user.display_name(),
      'this_user_display_name': this_user.display_name(),
      'match_count': len(intersection_data),
      'this_user_short_url': this_user_short_url,
      'homepage_url': self._generate_absolute_url(''),
    }
    mail.send_mail(sender='Intersquares <app@intersquares.com>',
                  to='%s <%s>' % (
                      other_user.display_name(), other_user.email_address),
                  subject='Intersquares match with %s' %
                      this_user.display_name(),
                  body='''Hi %(other_user_display_name)s:

%(this_user_display_name)s just used Intersquares to see where you would have
met, and it looks like you have %(match_count)d checkins in common. To see
them for yourself, visit:

%(this_user_short_url)s

To see other intersections, or to turn off these emails, visit:

%(homepage_url)s

Thanks,
Intersquares Team (i.e. Mihai P.)
''' % message_data)

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

class RecentIntersectionsHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    this_user = self._get_user()

    base_intersections, search_intersections = \
        data.intersection.Intersection.get_for_user(this_user)

    self._write_template(
        'recent-intersections.snippet', {
            'base_intersections': base_intersections,
            'search_intersections': search_intersections
        })
