from google.appengine.ext import db

import data.user

class Intersection(db.Model):
  base_foursquare_id = db.StringProperty(required=True)
  base_external_id = db.StringProperty(required=True, indexed=False)
  search_foursquare_id = db.StringProperty(required=True)
  search_external_id = db.StringProperty(required=True, indexed=False)
  date = db.DateTimeProperty(auto_now_add=True, indexed=False)
  match_count = db.IntegerProperty(indexed=False)
  emailed = db.BooleanProperty(indexed=False)

  @staticmethod
  def create_or_update(
      base_foursquare_id,
      search_foursquare_id,
      base_external_id,
      search_external_id,
      match_count):
    existing = Intersection.all().filter(
        'base_foursquare_id = ', base_foursquare_id).filter(
        'search_foursquare_id = ', search_foursquare_id).get()
    if existing:
      existing.match_count = match_count
      return existing
    return Intersection(
        base_foursquare_id = base_foursquare_id,
        search_foursquare_id = search_foursquare_id,
        base_external_id = base_external_id,
        search_external_id = search_external_id,
        match_count = match_count)

  @staticmethod
  def get_by_base_foursquare_id(base_foursquare_id):
    return Intersection.all().filter(
        'base_foursquare_id = ', base_foursquare_id).fetch(limit=100)

  @staticmethod
  def get_by_search_foursquare_id(search_foursquare_id):
    return Intersection.all().filter(
        'search_foursquare_id = ', search_foursquare_id).fetch(limit=100)

  @staticmethod
  def get_for_user(user):
    users_by_foursquare_id = {user.foursquare_id: user}

    def fetch_user(foursquare_id):
      if foursquare_id not in users_by_foursquare_id:
        users_by_foursquare_id[foursquare_id] = \
            data.user.User.get_by_foursquare_id(foursquare_id, None)
      return users_by_foursquare_id[foursquare_id]

    def fetch_intersections_users(intersections):
      for intersection in intersections:
        intersection.base_foursquare_user = \
            fetch_user(intersection.base_foursquare_id)
        intersection.search_foursquare_user = \
            fetch_user(intersection.search_foursquare_id)

    base_intersections = (data.intersection.Intersection.
        get_by_base_foursquare_id(user.foursquare_id))
    base_intersections = [i for i in base_intersections
        if i.search_foursquare_id != user.foursquare_id]
    fetch_intersections_users(base_intersections)
    search_intersections = (data.intersection.Intersection.
        get_by_search_foursquare_id(user.foursquare_id))
    search_intersections = [i for i in search_intersections
        if i.base_foursquare_id != user.foursquare_id]
    fetch_intersections_users(search_intersections)

    return base_intersections, search_intersections
