(function (global) {
  var csrfToken = null

  function apiBase() {
    return (global.FACULTYLINK_API_BASE || 'http://127.0.0.1:5000') + '/api/v1'
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

  function reviewerFetch(path, options) {
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
      }).then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, status: response.status, body: body }
        })
      })
    })
  }

  global.FacultyLinkReviewerHttp = {
    apiBase: apiBase,
    ensureCsrf: ensureCsrf,
    reviewerFetch: reviewerFetch,
    resetCsrf: function () {
      csrfToken = null
    },
  }
})(window)
