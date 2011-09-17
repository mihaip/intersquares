import datetime
import logging

class Checkin(object):
  def __init__(self, json_data):
    self.id = json_data['id']
    self.type = json_data['type']
    self.private = 'private' in json_data
    self.timezone = json_data.get('timeZone', None)
    self.venue_id = json_data.get('venue', {}).get('id', None)
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
