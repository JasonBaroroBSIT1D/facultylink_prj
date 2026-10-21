(function () {
  var session = window.FacultyLinkMockAuth && FacultyLinkMockAuth.loadSession()
  if (!session || session.role !== 'admin') {
    window.location.replace('../login.html')
  }
})()
