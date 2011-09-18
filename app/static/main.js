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

function loadIntersections(externalId, successCallback) {
  goog.net.XhrIo.send(
      '/checkins/intersect/data?external_id=' + encodeURIComponent(externalId),
      function(event) {
        successCallback(event.target.getResponseText());
      });
}

function fetchRecentIntersections(successCallback) {
 goog.net.XhrIo.send(
      '/checkins/intersect/recent',
      function(event) {
        successCallback(event.target.getResponseText());
      });
}

function printEmail(opt_anchorText) {
  var a = [109, 105, 104, 97, 105, 64, 112, 101, 114, 115, 105, 115, 116,
      101, 110, 116, 46, 105, 110, 102, 111];
  var b = [];
  for (var i = 0; i < a.length; i++) {
    b.push(String.fromCharCode(a[i]));
  }
  b = b.join('');
  document.write('<' + 'a href="mailto:' + b + '">' +
                 (opt_anchorText || b) +
                 '<' + '/a>');
};
