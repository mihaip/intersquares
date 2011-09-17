import calendar
import datetime
import logging

import base.interval_tree

HERE_NOW_DELTA = datetime.timedelta(hours=2)
TRAVEL_TIME_DELTA = datetime.timedelta(minutes=5)

class CheckinInterval(object):
  def __init__(self, checkin, next_checkin):
      # TODO(mihaip): so many datetime conversions is probably a bad idea
      self.start = calendar.timegm(checkin.timestamp.timetuple())
      end_timestamp = checkin.timestamp + HERE_NOW_DELTA
      if next_checkin and end_timestamp > next_checkin.timestamp:
        # TODO(mihaip): travel time should be a function of distance
        end_timestamp = next_checkin.timestamp - TRAVEL_TIME_DELTA
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

class Checkin(object):
  def __init__(self, json_data):
    self.id = json_data['id']
    self.type = json_data['type']
    self.private = 'private' in json_data
    self.timezone = json_data.get('timeZone', None)
    self.venue_id = json_data.get('venue', {}).get('id', None)
    self.venue_name = json_data.get('venue', {}).get('name', None)
    self.timestamp = datetime.datetime.utcfromtimestamp(json_data['createdAt'])

    # TODO(mihaip): shout, comments, photos, overlaps

  def should_use(self):
    return self.type == 'checkin' and not self.private and self.venue_id

class Checkins(object):
  def __init__(self):
    self._checkins_by_id = {}

  def update(self, api):
    # TODO(mihaip): pagination, look at oldest/newest timestamp of current
    # data.
    checkins_json_data = api.get('users/self/checkins', {'limit': 250})

    for checkin_json_data in checkins_json_data['checkins']['items']:
      checkin = Checkin(checkin_json_data)
      self._checkins_by_id[checkin.id] = checkin

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

  def intersection(self, other_checkins):
    return _compute_intersection(
        self._checkins_by_id.values(),
        other_checkins._checkins_by_id.values())
