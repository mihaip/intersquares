import calendar
import datetime
import logging

import pytz

import base.interval_tree
import data.checkin

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

class Checkins(object):
  def __init__(self):
    self._checkins_by_id = {}

  def _fetch(self, api, after_timestamp=None, before_timestamp=None):
    params = {'limit': 250}
    if after_timestamp:
      params['afterTimestamp'] = calendar.timegm(after_timestamp.timetuple())
    if before_timestamp:
      params['beforeTimestamp'] = calendar.timegm(before_timestamp.timetuple())
    checkins_json_data = api.get('users/self/checkins', params)

    new_count = 0
    for checkin_json_data in checkins_json_data['checkins']['items']:
      checkin = data.checkin.Checkin(checkin_json_data)
      if checkin.id not in self._checkins_by_id:
        new_count += 1
      self._checkins_by_id[checkin.id] = checkin

    return new_count

  def fetch_newer(self, api):
    after_timestamp = self.length() and self.newest().timestamp or None
    return self._fetch(api, after_timestamp=after_timestamp) > 0

  def fetch_older(self, api):
    if self.length():
      return self._fetch(
          api,
          after_timestamp=self.newest().timestamp,
          before_timestamp=END_OF_TIME) > 0
    else:
      return self._fetch(api, before_timestamp=END_OF_TIME) > 0

  def length(self):
    return len(self._checkins_by_id)

  def oldest(self):
    oldest = None
    for checkin in self._checkins_by_id.values():
      if not oldest or oldest.timestamp > checkin.timestamp:
        oldest = checkin
    return oldest

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
    for checkin in sorted_checkins[250:]:
      self._checkins_by_id[checkin.id] = checkin

  def intersection(self, other_checkins):
    return _compute_intersection(
        self._checkins_by_id.values(),
        other_checkins._checkins_by_id.values())
