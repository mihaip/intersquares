import urlparse

import base.handlers
import data.session
import data.user

class IndexHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    user = self._get_user()

    short_url = self._generate_absolute_url('i/' + self._session.external_id)
    tweet_text = 'Use Foursquare? See where we would have met: %s' % short_url
    # We don't just generate the QR code image URL, since we want to control
    # the viewport that it's rendered with (QrCodeIntersectHandler does that)
    qr_code_url = 'q/' + self._session.external_id

    mihai_user = None
    mihai_short_url = None
    if user.foursquare_id != '2118':
      mihai_user = data.user.User.get_by_foursquare_id('2118', None)
      if mihai_user:
        mihai_session = data.session.Session.get_by_foursquare_id('2118')
        mihai_short_url = self._generate_absolute_url('i/' + mihai_session.external_id)

    self._write_template(
        'index-signed-in.html', {
          'session': self._session,
          'user': user,
          'short_url': short_url,
          'tweet_text': tweet_text,
          'qr_code_url': qr_code_url,
          'mihai_user': mihai_user,
          'mihai_short_url': mihai_short_url,
        })

  def _get_signed_out(self):
    self._write_template('index-signed-out.html')
