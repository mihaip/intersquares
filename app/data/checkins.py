import calendar
import datetime
import logging

from google.appengine.ext import db
import pytz

import base.interval_tree
import base.util
import data.checkin
import data.venue

# If we're mid-update and the user hasn't been modified, the update process
# is probably stuck, so try to restart it.
_MAX_IN_UPDATE_DATA_AGE = datetime.timedelta(minutes=1)
_MAX_CHECKIN_DATA_AGE = datetime.timedelta(hours=1)

_HERE_NOW_DELTA = datetime.timedelta(hours=3)
_TRAVEL_TIME_DELTA = datetime.timedelta(minutes=5)

# Date far into the future (2038) passed in as a beforeTimestamp to trigger
# consistent paging behavior (otherwise queries without beforeTimestamp
# return in reverse-chronological order, and those with it return in
# chronological order).
END_OF_TIME = datetime.datetime.fromtimestamp((2 << 30) - 1, pytz.UTC)

class CheckinInterval(object):
  def __init__(self, checkin, next_checkin):
      # TODO(mihaip): so many datetime conversions is probably a bad idea
      self.start = calendar.timegm(checkin.timestamp.timetuple())
      end_timestamp = checkin.timestamp + _HERE_NOW_DELTA
      if next_checkin and end_timestamp > next_checkin.timestamp:
        # TODO(mihaip): travel time should be a function of distance
        end_timestamp = next_checkin.timestamp - _TRAVEL_TIME_DELTA
      self.stop = calendar.timegm(end_timestamp.timetuple())
      self.checkin = checkin

def _get_intervals(checkins):
  sorted_checkins = sorted(checkins, key=lambda checkin: checkin.timestamp)
  intervals = []
  for i in xrange(0, len(sorted_checkins) - 1):
    intervals.append(
        CheckinInterval(sorted_checkins[i], sorted_checkins[i + 1]))

  if len(sorted_checkins):
    intervals.append(CheckinInterval(sorted_checkins[-1], None))

  return intervals

def _compute_intersection(base_checkins, search_checkins):
  # The only checkins that we need to intersect are those that come from venues
  # that appear in both sets and that are not private.
  common_venue_ids = set([c.venue_id for c in base_checkins]).intersection(
      [c.venue_id for c in search_checkins])
  checkin_filter = lambda c: c.should_use() and c.venue_id in common_venue_ids
  base_checkins = filter(checkin_filter, base_checkins)
  search_checkins = filter(checkin_filter, search_checkins)

  logging.info('Intersecting %d and %d checkins' % (
      len(base_checkins), len(search_checkins)))

  base_intervals = _get_intervals(base_checkins)
  search_intervals = _get_intervals(search_checkins)

  base_tree = base.interval_tree.IntervalTree(base_intervals)

  intersection = []
  for search_interval in search_intervals:
    overlap = base_tree.find(search_interval.start, search_interval.stop)
    for base_interval in overlap:
      if base_interval.checkin.venue_id == search_interval.checkin.venue_id:
        intersection.append((base_interval.checkin, search_interval.checkin))

  return intersection

class CheckinsData(object):
  def __init__(self):
    self._checkins_by_id = {}

  def append_api_response(self, checkins_json_data):
    seen_venue_ids = set()
    new_count = 0
    for checkin_json_data in checkins_json_data['checkins']['items']:
      checkin = data.checkin.Checkin(checkin_json_data)

      if 'venue' in checkin_json_data:
        venue_json_data = checkin_json_data['venue']
        if 'id' in venue_json_data:
          venue_id = venue_json_data['id']
          if venue_id not in seen_venue_ids:
            data.venue.Venue.create_if_needed(venue_json_data)
            seen_venue_ids.add(venue_id)

      if checkin.id not in self._checkins_by_id:
        new_count += 1
      self._checkins_by_id[checkin.id] = checkin

    return new_count

  def length(self):
    return len(self._checkins_by_id)

  def checkins(self):
    return self._checkins_by_id.values()

  def newest(self):
    newest = None
    for checkin in self._checkins_by_id.values():
      if not newest or newest.timestamp < checkin.timestamp:
        newest = checkin
    return newest

  def drop_old_checkins(self):
    sorted_checkins = sorted(
        self._checkins_by_id.values(), key=lambda checkin: checkin.timestamp)
    self._checkins_by_id = {}
    for checkin in sorted_checkins[350:]:
      self._checkins_by_id[checkin.id] = checkin

class CheckinsDataProperty(base.util.PickledProperty):
  force_type = CheckinsData

class Checkins(db.Model):
  foursquare_id = db.StringProperty(required=True)
  last_update = db.DateTimeProperty(auto_now=True,indexed=False)
  is_updating = db.BooleanProperty(indexed=False)
  data = CheckinsDataProperty()

  def length(self):
    return self.data and self.data.length() or 0

  def update_needed(self):
    logging.info('Checking if update is needed for %s', self.foursquare_id)
    if not self.length():
      logging.info('  Yes, because there are no checkins')
      return True

    last_update_delta = datetime.datetime.utcnow() - self.last_update
    if self.is_updating and last_update_delta > _MAX_IN_UPDATE_DATA_AGE:
      logging.info('  Yes, because there is an update and the age is %s',
          str(last_update_delta))
      return True

    if last_update_delta > _MAX_CHECKIN_DATA_AGE:
      logging.info('  Yes, because the data age is %s', str(last_update_delta))
      return True

    logging.info('  No')
    return False

  def fetch_newer(self, api):
    after_timestamp = self.length() and self.data.newest().timestamp or None
    return self._fetch(api, after_timestamp=after_timestamp) > 0

  def fetch_older(self, api):
    if self.length():
      return self._fetch(
          api,
          after_timestamp=self.data.newest().timestamp,
          before_timestamp=END_OF_TIME) > 0
    else:
      return self._fetch(api, before_timestamp=END_OF_TIME) > 0

  def clear(self):
    self.data = None

  def drop_old_checkins(self):
    if self.data:
      self.data.drop_old_checkins()

  def intersection(self, other_checkins):
    logging.info('Interection between %s (%d) and %s (%d)',
        self.foursquare_id, self.length(),
        other_checkins.foursquare_id, other_checkins.length())
    if self.length() and other_checkins.length():
      return _compute_intersection(
          self.data.checkins(), other_checkins.data.checkins())
    else:
      return []

  def _fetch(self, api, after_timestamp=None, before_timestamp=None):
    params = {'limit': 250}
    if after_timestamp:
      params['afterTimestamp'] = calendar.timegm(after_timestamp.timetuple())
    if before_timestamp:
      params['beforeTimestamp'] = calendar.timegm(before_timestamp.timetuple())

    if not self.data:
      self.data = CheckinsData()

    return self.data.append_api_response(api.get('users/self/checkins', params))

  @staticmethod
  def get_by_foursquare_id(foursquare_id):
    checkins = Checkins.all().filter('foursquare_id = ', foursquare_id).get()

    if not checkins:
      checkins = Checkins(foursquare_id = foursquare_id)
      checkins.put()

    return checkins

  @staticmethod
  def get_for_user(user):
    return Checkins.get_by_foursquare_id(user.foursquare_id)
