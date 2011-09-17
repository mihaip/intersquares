import urlparse

import base.handlers

class IndexHandler(base.handlers.ApiHandler):
  def _get_signed_in(self):
    user = self._get_user()

    tweet_text = 'Use Fourquare? See where we would have met: %s' % (
        self._generate_absolute_url('i/' + self._session.external_id))

    self._write_template(
        'index-signed-in.html', {
          'session': self._session,
          'user': user,
          'tweet_text': tweet_text
        })

  def _get_signed_out(self):
    self._write_template('index-signed-out.html')
