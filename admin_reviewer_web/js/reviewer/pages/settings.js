window.ReviewerPageInit = function (el) {
  FacultyLinkAccountSettingsPage.mount(el, {
    roleLabel: 'Reviewer',
    requiredRole: 'reviewer',
    loginPath: '../login.html',
    ensureCsrf: function () {
      return FacultyLinkReviewerHttp.ensureCsrf()
    },
    fetchUser: function () {
      return FacultyLinkReviewerApi.getCurrentUser()
    },
    changePassword: function (current, next) {
      return FacultyLinkReviewerApi.changePassword(current, next)
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
