window.AdminPageInit = function (el) {
  FacultyLinkAccountSettingsPage.mount(el, {
    roleLabel: 'Administrator',
    requiredRole: 'admin',
    loginPath: '../login.html',
    ensureCsrf: function () {
      return FacultyLinkAdminHttp.ensureCsrf()
    },
    fetchUser: function () {
      return FacultyLinkAdminApi.getCurrentUser()
    },
    changePassword: function (current, next) {
      return FacultyLinkAdminApi.changePassword(current, next)
    },
    signOut: function () {
      return FacultyLinkMockAuth.signOut()
    },
    onUserLoaded: function (user) {
      FacultyLinkMockAuth.saveSession({
        email: user.email,
        role: user.role,
        displayName: user.full_name,
        userId: user.user_id,
      })
    },
  })
}
