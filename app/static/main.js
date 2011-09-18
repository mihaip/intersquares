// TODO(mihaip): Start using Plovr

goog.require('goog.dom');
goog.require('goog.net.XhrIo');

function updateCheckins(indicatorNode, successCallback) {
  indicatorNode.innerText = 'Loading your checkins...';
  goog.dom.classes.addRemove(indicatorNode, 'faded-out', 'faded-in');

  goog.net.XhrIo.send(
      '/checkins/update',
      function() {
        setTimeout(
            goog.partial(updateProgress, indicatorNode, successCallback),
            1000);
      });
}

function updateProgress(indicatorNode, successCallback) {
  goog.net.XhrIo.send(
      '/checkins/update/state',
      function(event) {
        var json = event.target.getResponseJson();

        if (json.is_updating) {
          indicatorNode.innerText =
              'Loading your checkins (got ' + json.checkin_count +
              ' so far)...';
          setTimeout(
              goog.partial(updateProgress, indicatorNode, successCallback),
              1000);
        } else {
          indicatorNode.innerText =
              'OK, your ' + json.checkin_count +
              ' checkins are now all loaded.';
          successCallback();
        }
      });
}
