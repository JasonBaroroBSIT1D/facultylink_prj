(function () {
  if (!window.FacultyLinkMockAuth) {
    window.location.replace('../login.html')
    return
  }
  window.FacultyLinkAdminAuthReady = FacultyLinkMockAuth.ensureSession('admin').then(function (ok) {
    if (!ok) {
      window.location.replace('../login.html')
      return false
    }
    return FacultyLinkMockAuth.fetchMe().then(function (user) {
      if (!user || user.role !== 'admin') {
        window.location.replace('../login.html')
        return false
      }
      FacultyLinkMockAuth.saveSession({
        email: user.email,
        role: user.role,
        displayName: user.full_name,
        userId: user.user_id,
      })
      return true
    })
  })
})()
