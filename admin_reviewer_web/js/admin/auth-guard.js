(function () {
  if (!window.FacultyLinkMockAuth) {
    window.location.replace('../login.html')
    return
  }
  FacultyLinkMockAuth.ensureSession('admin').then(function (ok) {
    if (!ok) window.location.replace('../login.html')
  })
})()
