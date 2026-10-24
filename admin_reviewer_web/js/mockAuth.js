/**
 * FacultyLink web authentication — Flask API + sessionStorage profile cache only.
 * Access tokens are HttpOnly cookies (not stored in localStorage/sessionStorage).
 */
(function (global) {
  const PROFILE_KEY = 'facultylink_user_profile'
  const API_BASE = function () {
    if (global.FacultyLinkApiOrigin) return global.FacultyLinkApiOrigin()
    var loc = global.location
    if (loc && loc.protocol && loc.protocol.indexOf('http') === 0 && loc.host) {
      return loc.origin
    }
    return global.FACULTYLINK_API_BASE || 'http://127.0.0.1:5000'
  }

  function saveSession(profile) {
    sessionStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
  }

  function loadSession() {
    const raw = sessionStorage.getItem(PROFILE_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw)
    } catch {
      return null
    }
  }

  function clearSession() {
    sessionStorage.removeItem(PROFILE_KEY)
  }

  function signIn(email, password) {
    return fetch(API_BASE() + '/api/v1/auth/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ email: email.trim(), password: password, client: 'web' }),
    })
      .then(function (response) {
        return response.json().then(function (body) {
          return { response: response, body: body }
        })
      })
      .then(function (result) {
        if (!result.response.ok) {
          var message = result.body.message || 'Sign in failed. Check your credentials and try again.'
          if (result.response.status === 401) {
            message = result.body.message || 'Invalid email or password.'
          }
          return {
            ok: false,
            message: message,
          }
        }
        var user = result.body.user
        return {
          ok: true,
          role: user.role,
          displayName: user.full_name,
          email: user.email,
          user: user,
          mustChangePassword: !!(result.body.must_change_password || user.must_change_password),
        }
      })
      .catch(function () {
        return {
          ok: false,
          message: 'Unable to reach the FacultyLink API. Start the Flask server and try again.',
        }
      })
  }

  function fetchMe() {
    return fetch(API_BASE() + '/api/v1/auth/me', {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
      .then(function (response) {
        if (!response.ok) return null
        return response.json().then(function (body) {
          var user = body.user
          if (user && (user.must_change_password || user.must_set_password)) {
            var path = global.location.pathname || ''
            if (path.indexOf('change-password-required.html') < 0) {
              global.location.href = 'change-password-required.html'
            }
          }
          return user
        })
      })
      .catch(function () {
        return null
      })
  }

  function ensureSession(requiredRole) {
    return fetchMe().then(function (user) {
      if (!user) {
        clearSession()
        return false
      }
      saveSession({
        email: user.email,
        role: user.role,
        displayName: user.full_name,
      })
      if (requiredRole && user.role !== requiredRole) {
        return false
      }
      return true
    })
  }

  function signOut() {
    var csrfReady =
      global.FacultyLinkAdminHttp && global.FacultyLinkAdminHttp.ensureCsrf
        ? global.FacultyLinkAdminHttp.ensureCsrf()
        : Promise.resolve(null)
    return csrfReady
      .then(function (token) {
        var headers = { Accept: 'application/json' }
        if (token) headers['X-CSRF-Token'] = token
        return fetch(API_BASE() + '/api/v1/auth/logout', {
          method: 'POST',
          credentials: 'include',
          headers: headers,
        })
      })
      .finally(function () {
        clearSession()
        if (global.FacultyLinkAdminHttp && global.FacultyLinkAdminHttp.resetCsrf) {
          global.FacultyLinkAdminHttp.resetCsrf()
        }
      })
  }

  global.FacultyLinkMockAuth = {
    signIn: signIn,
    saveSession: saveSession,
    loadSession: loadSession,
    clearSession: clearSession,
    fetchMe: fetchMe,
    ensureSession: ensureSession,
    signOut: signOut,
  }
})(window)
