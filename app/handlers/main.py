import urlparse

import base.handlers

class IndexHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    user = self._get_user()

    short_url = self._generate_absolute_url('i/' + self._session.external_id)
    tweet_text = 'Use Fourquare? See where we would have met: %s' % short_url
    # We don't just generate the QR code image URL, since we want to control
    # the viewport that it's rendered with (QrCodeIntersectHandler does that)
    qr_code_url = 'q/' + self._session.external_id

    self._write_template(
        'index-signed-in.html', {
          'session': self._session,
          'user': user,
          'short_url': short_url,
          'tweet_text': tweet_text,
          'qr_code_url': qr_code_url,
        })

  def _get_signed_out(self):
    self._write_template('index-signed-out.html')
