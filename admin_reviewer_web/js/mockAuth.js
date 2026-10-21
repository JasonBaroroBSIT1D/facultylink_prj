/**
 * MOCK AUTHENTICATION — frontend UI testing only.
 * Replace with Flask API integration via backend auth endpoints.
 */
(function (global) {
  const STORAGE_KEY = 'facultylink_mock_session'

  const MOCK_ACCOUNTS = {
    'admin@facultylink.edu': {
      password: 'demo-admin',
      role: 'admin',
      displayName: 'System Administrator',
    },
    'reviewer@facultylink.edu': {
      password: 'demo-reviewer',
      role: 'reviewer',
      displayName: 'Faculty Reviewer',
    },
  }

  function signIn(email, password) {
    return new Promise(function (resolve) {
      setTimeout(function () {
        const account = MOCK_ACCOUNTS[email.trim().toLowerCase()]
        if (!account || account.password !== password) {
          resolve({
            ok: false,
            message:
              'Invalid email or password. Use demo accounts shown below for UI testing.',
          })
          return
        }
        resolve({
          ok: true,
          role: account.role,
          displayName: account.displayName,
        })
      }, 600)
    })
  }

  function saveSession(session) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  }

  function loadSession() {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw)
    } catch {
      return null
    }
  }

  function clearSession() {
    sessionStorage.removeItem(STORAGE_KEY)
  }

  global.FacultyLinkMockAuth = {
    signIn,
    saveSession,
    loadSession,
    clearSession,
  }
})(window)
