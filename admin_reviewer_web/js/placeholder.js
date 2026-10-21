document.addEventListener('DOMContentLoaded', function () {
  if (window.FacultyLinkUI) {
    FacultyLinkUI.mountLogos()
  }

  var sessionEl = document.getElementById('session-info')
  var session = window.FacultyLinkMockAuth && FacultyLinkMockAuth.loadSession()
  if (sessionEl && session) {
    sessionEl.textContent = session.displayName
  }

  var signOut = document.getElementById('sign-out')
  if (signOut) {
    signOut.addEventListener('click', function () {
      FacultyLinkMockAuth.clearSession()
    })
  }
})
