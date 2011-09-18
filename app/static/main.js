// TODO(mihaip): Start using Plovr

goog.require('goog.dom');
goog.require('goog.net.XhrIo');

function updateCheckins(indicatorParentNode, successCallback) {
  var indicatorNode = goog.dom.$dom('div', {'id': 'checkins-progress'});
  indicatorNode.innerText = 'Fetching checkins...';
  indicatorParentNode.appendChild(indicatorNode);

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
          indicatorNode.innerText = 'Got ' + json.checkin_count + ' checkins...';
          setTimeout(
              goog.partial(updateProgress, indicatorNode, successCallback),
              1000);
        } else {
          indicatorNode.innerText = 'Got ' + json.checkin_count + ' checkins.';
          successCallback();
        }
      });
}
