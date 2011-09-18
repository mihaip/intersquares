from google.appengine.ext import db

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
