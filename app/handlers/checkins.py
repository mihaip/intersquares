import logging
import urllib

from google.appengine.api import mail
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.runtime import apiproxy_errors

import base.handlers
import data.checkins
import data.intersection
import data.session
import data.user
import data.venue

class UpdateCheckinsHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    checkins = self._get_checkins()

    if checkins.update_needed():
      direction = checkins.length() and 'forward' or 'backward'
      checkins.is_updating = True
      checkins.put()

      taskqueue.add(
          queue_name='update-checkins',
          url='/tasks/checkins/update',
          params={
            'oauth_token': self._session.oauth_token,
            'foursquare_id': checkins.foursquare_id,
            'direction': direction
          })

    self.response.out.write('OK')

class ReloadCheckinsAdminHandler(base.handlers.BaseHandler):
  def get(self):
    update_count = 0
    for session in data.session.Session.all():
      update_count += 1
      taskqueue.add(
          queue_name='clear-checkins',
          url='/tasks/checkins/clear',
          params={
            'oauth_token': session.oauth_token,
            'foursquare_id': session.foursquare_id,
          })
    self.response.out.write('Kicked off %d updates' % update_count)

class ClearCheckinsTaskHandler(base.handlers.BaseHandler):
  def post(self):
    foursquare_id = self.request.get('foursquare_id')
    oauth_token = self.request.get('oauth_token')
    logging.info('Clearing checkins for %s', foursquare_id)

    # Clear user data and regenerate it from Foursquare
    user = data.user.User.get_by_foursquare_id(foursquare_id, None)
    user.delete()
    user = data.user.User.get_by_foursquare_id(
        foursquare_id, base.api.Api(oauth_token))

    # Clear checkin data and kick off the task to update it
    checkins = data.checkins.Checkins.get_by_foursquare_id(foursquare_id)
    checkins.clear()
    checkins.is_updating = True
    checkins.put()
    taskqueue.add(
        queue_name='update-checkins',
        url='/tasks/checkins/update',
        params={
          'oauth_token': oauth_token,
          'foursquare_id': foursquare_id,
          'direction': 'backward'
        })

class UpdateCheckinsTaskHandler(base.handlers.BaseHandler):
  def post(self):
    oauth_token = self.request.get('oauth_token')
    api = base.api.Api(oauth_token)
    checkins = data.checkins.Checkins.get_by_foursquare_id(
        self.request.get('foursquare_id'))
    direction = self.request.get('direction')

    logging.info('Updating checkins for %s (direction: %s)',
        checkins.foursquare_id, direction)

    if direction == 'forward':
      has_more = checkins.fetch_newer(api)
    else:
      has_more = checkins.fetch_older(api)

    if not has_more:
      checkins.is_updating = False

    try:
      checkins.put()
    except (db.BadRequestError, apiproxy_errors.RequestTooLargeError), err:
      logging.exception(err)
      logging.error(
          '%s has too many checkins (%d), dropping some',
          checkins.foursquare_id, checkins.length())
      checkins.drop_old_checkins()
      logging.error(
          '%s now has %d checkins',
          checkins.foursquare_id, checkins.length())
      checkins.put()

    if has_more:
      taskqueue.add(
          queue_name='update-checkins',
          url='/tasks/checkins/update',
          params={
            'oauth_token': oauth_token,
            'foursquare_id': checkins.foursquare_id,
            'direction': direction
          })

    self.response.out.write('OK')

class UpdateCheckinsStateHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    checkins = self._get_checkins()

    logging.info('Getting update state for %s', checkins.foursquare_id)

    return self._write_json({
      'is_updating': checkins.is_updating or False,
      'checkin_count': checkins.length(),
    })

class ClearCheckinsHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    checkins = self._get_checkins()
    checkins.clear()
    checkins.put()
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
    other_user_checkins = data.checkins.Checkins.get_for_user(other_user)

    connect_url = '/4sq/connect?continue=%s' % urllib.quote(self.request.url)

    self._write_template(
        'intersections-signed-out.html', {
            'other_user': other_user,
            'other_user_checkins': other_user_checkins,
            'connect_url': connect_url,
        })

class IntersectCheckinsDataHandler(BaseIntersectHandler):
  def _get_signed_in(self):
    this_user = self._get_user()
    other_user = self._get_other_user()
    if not other_user:
      return

    this_user_checkins = data.checkins.Checkins.get_for_user(this_user)

    short_url = self._generate_absolute_url('i/' + self._session.external_id)
    tweet_text = 'Use Foursquare? See where we would have met: %s' % short_url

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
              'this_user_checkins': this_user_checkins,
              'short_url': short_url,
              'tweet_text': tweet_text,
              'mihai_user': mihai_user,
              'mihai_short_url': mihai_short_url,
          })
      return

    other_user_checkins = data.checkins.Checkins.get_for_user(other_user)
    logging.info('Loaded other_user (%s) checkins (%d)', other_user.foursquare_id, other_user_checkins.length())
    intersection_raw_data = this_user_checkins.intersection(other_user_checkins)

    venue_ids = list(set([t.venue_id for t,o in intersection_raw_data]))
    venues = data.venue.Venue.get_by_key_name(key_names = venue_ids)
    venues_by_venue_id = dict((v.venue_id, v) for v in venues if v)

    intersection_data = []
    for this_user_checkin, other_user_checkin in intersection_raw_data:
      intersection_data.append((
          this_user_checkin,
          other_user_checkin,
          venues_by_venue_id[this_user_checkin.venue_id]))

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
            'this_user_checkins': this_user_checkins,
            'other_user_checkins': other_user_checkins,
            'short_url': short_url,
            'tweet_text': tweet_text,
          })
      return

    self._write_template(
        'intersections-data.snippet', {
            'this_user': this_user,
            'other_user': other_user,
            'this_user_checkins': this_user_checkins,
            'other_user_checkins': other_user_checkins,
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
