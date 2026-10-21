window.AdminPageInit = function (el, helpers) {
  FacultyLinkAdminApi.listDocumentMonitoring().then(function (rows) {
    var body = rows
      .map(function (d) {
        return (
          '<tr><td>' +
          d.id +
          '</td><td>' +
          d.faculty +
          '</td><td>' +
          d.kra +
          '</td><td>' +
          d.criterion +
          '</td><td>' +
          helpers.statusBadge(d.status) +
          '</td><td>' +
          helpers.statusBadge(d.ocr) +
          '</td><td>' +
          d.uploaded +
          '</td><td><button type="button" class="fl-btn fl-btn--ghost" style="padding:6px 12px;font-size:0.8rem" disabled>Open</button></td></tr>'
        )
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Document &amp; Evaluation Monitoring</h1>' +
      '<p class="admin-page-desc">Track uploads, OCR processing, rule-based validation, and approval status across faculty.</p>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Recent submissions</h2><span class="fl-badge fl-badge--warning">Mock monitoring</span></div>' +
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Document</th><th>Faculty</th><th>KRA</th><th>Criterion</th><th>Status</th><th>OCR</th><th>Uploaded</th><th></th></tr></thead><tbody>' +
      body +
      '</tbody></table></div></div>'
  })
}
