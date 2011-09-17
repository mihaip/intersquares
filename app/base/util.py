import base64
import uuid

def generate_id(prefix):
  return prefix + base64.urlsafe_b64encode(
      uuid.uuid4().bytes).replace('=', '')
