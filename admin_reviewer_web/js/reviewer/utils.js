(function (global) {
  function checkIcon(result) {
    var cls =
      result === 'pass' ? 'pass' : result === 'warn' ? 'warn' : result === 'fail' ? 'fail' : 'warn'
    var sym = result === 'pass' ? '✓' : result === 'fail' ? '✕' : '!'
    return '<span class="reviewer-check-icon reviewer-check-icon--' + cls + '">' + sym + '</span>'
  }

  function queryParam(name) {
    return new URLSearchParams(window.location.search).get(name)
  }

  global.FacultyLinkReviewerUtils = { checkIcon: checkIcon, queryParam: queryParam }
})(window)
