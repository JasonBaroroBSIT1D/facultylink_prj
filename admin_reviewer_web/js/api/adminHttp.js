(function (global) {
  var csrfToken = null

  function apiOrigin() {
    if (global.FacultyLinkApiOrigin) return global.FacultyLinkApiOrigin()
    var loc = global.location
    if (loc && loc.protocol && loc.protocol.indexOf('http') === 0 && loc.host) {
      return loc.origin
    }
    return global.FACULTYLINK_API_BASE || 'http://127.0.0.1:5000'
  }

  function apiBase() {
    return apiOrigin() + '/api/v1'
  }

  function readCsrfCookie() {
    var match = document.cookie.match(/(?:^|;\s*)facultylink_csrf=([^;]+)/)
    return match ? decodeURIComponent(match[1]) : null
  }

  function ensureCsrf() {
    var existing = csrfToken || readCsrfCookie()
    if (existing) {
      csrfToken = existing
      return Promise.resolve(csrfToken)
    }
    return fetch(apiBase() + '/auth/csrf', {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
      .then(function (response) {
        if (!response.ok) throw new Error('Unable to obtain CSRF token.')
        return response.json()
      })
      .then(function (body) {
        csrfToken = body.csrf_token || readCsrfCookie()
        return csrfToken
      })
  }

  function adminFetch(path, options) {
    options = options || {}
    var method = (options.method || 'GET').toUpperCase()
    var needsCsrf = method !== 'GET' && method !== 'HEAD'
    var run = needsCsrf ? ensureCsrf() : Promise.resolve(csrfToken)

    return run.then(function (token) {
      var headers = Object.assign(
        { Accept: 'application/json' },
        options.headers || {},
        options.body ? { 'Content-Type': 'application/json' } : {}
      )
      if (needsCsrf && token) headers['X-CSRF-Token'] = token
      return fetch(apiBase() + path, {
        method: method,
        credentials: 'include',
        headers: headers,
        body: options.body,
      })
        .then(function (response) {
          return response
            .json()
            .catch(function () {
              return { message: 'Unexpected server response.' }
            })
            .then(function (body) {
              return { ok: response.ok, status: response.status, body: body }
            })
        })
        .catch(function () {
          return Promise.reject(new Error('Unable to reach the FacultyLink API. Check that the server is running.'))
        })
    })
  }

  global.FacultyLinkAdminHttp = {
    apiBase: apiBase,
    ensureCsrf: ensureCsrf,
    adminFetch: adminFetch,
    resetCsrf: function () {
      csrfToken = null
    },
  }
})(window)
