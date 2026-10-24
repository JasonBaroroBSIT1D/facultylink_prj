(function () {
  function startShell() {
    var pageId = document.body.getAttribute('data-reviewer-page') || 'dashboard'
    var session = FacultyLinkMockAuth.loadSession()

    function statusBadge(status) {
      var map = {
        Active: 'success',
        Inactive: 'muted',
        'System Approved': 'success',
        'Needs Verification': 'warning',
        'Needs Revision': 'warning',
        Rejected: 'danger',
        Passed: 'success',
      }
      var tone = map[status] || 'info'
      if (status && status.indexOf('Awaiting') >= 0) tone = 'muted'
      return '<span class="fl-badge fl-badge--' + tone + '">' + status + '</span>'
    }

    function buildNav() {
      return FacultyLinkPortalNav.build(FacultyLinkReviewerNav, pageId)
    }

    function initials(name) {
      return (name || 'R')
        .split(' ')
        .map(function (p) {
          return p[0]
        })
        .slice(0, 2)
        .join('')
        .toUpperCase()
    }

    document.body.classList.add('admin-portal')
    document.body.innerHTML =
      '<div class="admin-layout">' +
      '<aside class="admin-sidebar" id="admin-sidebar" aria-label="reviewer navigation">' +
      '<div class="admin-sidebar__brand"><div data-fl-logo data-logo-mode="nav" data-variant="light" data-size="sm"></div>' +
      '<p style="margin:8px 0 0;font-size:0.75rem;opacity:0.75">Reviewer Portal</p></div>' +
      '<button type="button" class="admin-sidebar__close" id="admin-menu-close" aria-label="Close navigation">Close <span aria-hidden="true">&times;</span></button>' +
      '<nav tabindex="0" class="admin-sidebar__nav" aria-label="Reviewer">' +
      buildNav() +
      '</nav></aside>' +
      '<div class="admin-overlay" id="admin-overlay" aria-hidden="true"></div>' +
      '<div class="admin-main">' +
      '<header class="admin-header">' +
      '<button type="button" class="admin-header__menu" id="admin-menu-btn" aria-label="Open navigation" aria-controls="admin-sidebar" aria-expanded="false">' +
      '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>' +
      '<div class="admin-header__search"><input type="search" placeholder="Search documents, faculty…" aria-label="Search" disabled title="Coming soon" /></div>' +
      '<div class="admin-header__actions">' +
      '<a href="notifications.html" class="admin-icon-btn" aria-label="Notifications">' +
      '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M15 17h5l-1.4-1.4A2 2 0 0118 14.2V11a6 6 0 10-12 0v3.2c0 .5-.2 1-.6 1.4L4 17h5m6 0a3 3 0 11-6 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></a>' +
      '<div class="admin-profile"><div class="admin-profile__avatar">' +
      initials(session.displayName) +
      '</div><div><strong>' +
      (session.displayName || 'Reviewer') +
      '</strong><br /><span style="color:var(--fl-text-muted);font-size:0.75rem">' +
      (session.email || '') +
      '</span></div></div>' +
      '<button type="button" class="fl-btn fl-btn--ghost" id="reviewer-sign-out" style="padding:8px 14px">Sign Out</button>' +
      '</div></header>' +
      '<main class="admin-content" id="reviewer-content"></main></div></div>'

    FacultyLinkUI.mountLogos()
    FacultyLinkUI.initPortalNavigation()
    document.getElementById('reviewer-sign-out').addEventListener('click', function () {
      var done = function () {
        window.location.href = '../login.html'
      }
      if (FacultyLinkMockAuth.signOut) {
        FacultyLinkMockAuth.signOut().finally(done)
      } else {
        FacultyLinkMockAuth.clearSession()
        done()
      }
    })

    var container = document.getElementById('reviewer-content')
    if (typeof window.ReviewerPageInit === 'function') {
      window.ReviewerPageInit(container, { statusBadge: statusBadge })
    }
  }

  var ready = window.FacultyLinkReviewerAuthReady
  if (ready && typeof ready.then === 'function') {
    ready.then(function (ok) {
      if (ok) startShell()
    })
  } else {
    startShell()
  }
})()
