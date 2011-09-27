import base64
import logging
import pickle
import urllib
import uuid

from google.appengine.ext import db
from google.appengine.api import datastore_errors

def generate_id(prefix):
  return prefix + base64.urlsafe_b64encode(
      uuid.uuid4().bytes).replace('=', '')

class PickledProperty(db.Property):
    data_type = db.Blob
    force_type = None

    def __init__(
        self,
        verbose_name=None,
        name=None,
        default=None,
        required=False,
        validator=None,
        choices=None):
      db.Property.__init__(
          self,
          verbose_name=verbose_name,
          name=name,
          default=default,
          required=required,
          validator=validator,
          choices=choices,
          indexed=False)

    def validate(self, value):
      value = super(PickledProperty, self).validate(value)
      if value is not None and self.force_type and \
          not isinstance(value, self.force_type):
        raise datastore_errors.BadValueError(
            'Property %s must be of type "%s".' % (self.name,
                self.force_type))
      return value

    def get_value_for_datastore(self, model_instance):
      value = self.__get__(model_instance, model_instance.__class__)
      if value is not None:
        value = pickle.dumps(value)
        logging.info('Saved pickled value of length %d', len(value))
        return db.Blob(value)

    def make_value_from_datastore(self, value):
      if value is not None:
        logging.info('Loaded pickled value of length %d', len(value))
        return pickle.loads(str(value))

def encode_parameters(params):
  def encode(s):
    return isinstance(s, unicode) and s.encode('utf-8') or s

  encoded_params = {}
  for key, value in params.items():
    if isinstance(value, list):
      value = [encode(v) for v in value]
    else:
      value = encode(value)
    encoded_params[encode(key)] = value
  return urllib.urlencode(encoded_params, doseq=True)
