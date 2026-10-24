(function (global) {
  function resolveFacultyLinkApiOrigin() {
    var loc = global.location
    if (loc && loc.protocol && loc.protocol.indexOf('http') === 0 && loc.host) {
      return loc.origin
    }
    return 'http://127.0.0.1:5000'
  }

  global.FacultyLinkApiOrigin = function () {
    return global.FACULTYLINK_API_BASE || resolveFacultyLinkApiOrigin()
  }

  if (!global.FACULTYLINK_API_BASE) {
    global.FACULTYLINK_API_BASE = resolveFacultyLinkApiOrigin()
  }
})(window)
