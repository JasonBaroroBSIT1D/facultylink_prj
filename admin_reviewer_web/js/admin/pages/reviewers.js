window.AdminPageInit = function (el, helpers) {
  FacultyLinkAdminApi.listReviewers().then(function (rows) {
    var body = rows
      .map(function (r) {
        return (
          '<tr><td>' +
          r.id +
          '</td><td><strong>' +
          r.name +
          '</strong></td><td>' +
          r.role +
          '</td><td>' +
          r.assigned +
          '</td><td>' +
          r.queue +
          '</td><td>' +
          helpers.statusBadge(r.status) +
          '</td><td><button type="button" class="fl-btn fl-btn--ghost" style="padding:6px 12px;font-size:0.8rem" disabled>Assign</button></td></tr>'
        )
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Reviewer Management</h1>' +
      '<p class="admin-page-desc">Assign reviewers, balance workloads, and configure verification permissions.</p>' +
      '<div class="admin-toolbar"><button type="button" class="fl-btn fl-btn--primary" disabled>Invite Reviewer</button></div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Reviewers</h2></div>' +
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Name</th><th>Role</th><th>Assigned faculty</th><th>Queue</th><th>Status</th><th></th></tr></thead><tbody>' +
      body +
      '</tbody></table></div></div>'
  })
}
