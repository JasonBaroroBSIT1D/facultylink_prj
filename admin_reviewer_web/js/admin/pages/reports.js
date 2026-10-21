window.AdminPageInit = function (el) {
  FacultyLinkAdminApi.getReports().then(function (data) {
    var rows = data.items
      .map(function (r) {
        return (
          '<tr><td><strong>' +
          r.name +
          '</strong></td><td>' +
          r.period +
          '</td><td>' +
          r.format +
          '</td><td>' +
          r.lastRun +
          '</td><td><button type="button" class="fl-btn fl-btn--primary" style="padding:6px 14px;font-size:0.8rem" disabled>Generate</button></td></tr>'
        )
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Reports &amp; Analytics</h1>' +
      '<p class="admin-page-desc">Export operational and compliance reports once connected to PostgreSQL analytics endpoints.</p>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Available reports</h2></div>' +
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Report</th><th>Period</th><th>Format</th><th>Last run</th><th></th></tr></thead><tbody>' +
      rows +
      '</tbody></table></div></div>'
  })
}
