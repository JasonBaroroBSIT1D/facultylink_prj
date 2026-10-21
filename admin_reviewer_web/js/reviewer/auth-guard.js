(function () {
  var session = window.FacultyLinkMockAuth && FacultyLinkMockAuth.loadSession()
  if (!session || session.role !== 'reviewer') {
    window.location.replace('../login.html')
  }
})()
