window.AdminPageInit = function (el, helpers) {
  FacultyLinkAdminApi.listFaculty().then(function (rows) {
    var body = rows
      .map(function (f) {
        return (
          '<tr><td>' +
          f.id +
          '</td><td><strong>' +
          f.name +
          '</strong></td><td>' +
          f.department +
          '</td><td>' +
          f.rank +
          '</td><td>' +
          helpers.statusBadge(f.status) +
          '</td><td>' +
          f.documents +
          '</td><td>' +
          f.kraProgress +
          '</td><td><button type="button" class="fl-btn fl-btn--ghost" style="padding:6px 12px;font-size:0.8rem" disabled>View (API)</button></td></tr>'
        )
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Faculty Management</h1>' +
      '<p class="admin-page-desc">Register, monitor, and manage faculty accounts linked to self-assessment workflows.</p>' +
      '<div class="admin-toolbar"><button type="button" class="fl-btn fl-btn--primary" disabled>Add Faculty (Flask API)</button>' +
      '<button type="button" class="fl-btn fl-btn--ghost" disabled>Import CSV</button></div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Faculty roster</h2><span class="fl-badge fl-badge--info">Mock list</span></div>' +
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Rank</th><th>Status</th><th>Docs</th><th>KRA progress</th><th></th></tr></thead><tbody>' +
      body +
      '</tbody></table></div></div>'
  })
}
