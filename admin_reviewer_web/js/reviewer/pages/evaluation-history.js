window.ReviewerPageInit = function (el) {
  FacultyLinkReviewerApi.getEvaluationHistory().then(function (rows) {
    var body = rows
      .map(function (r) {
        return (
          '<tr><td>' +
          r.faculty +
          '</td><td>' +
          r.item +
          '</td><td>' +
          r.kra +
          '</td><td>' +
          r.previous +
          '</td><td>' +
          r.updated +
          '</td><td>' +
          r.action +
          '</td><td>' +
          r.remarks +
          '</td><td>' +
          r.when +
          '</td></tr>'
        )
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Evaluation History</h1>' +
      '<p class="admin-page-desc">Audit trail preview for reviewer actions and status changes (mock — future backend audit log).</p>' +
      '<div class="admin-filter-bar"><input type="search" id="hist-search" placeholder="Filter faculty…" /></div>' +
      '<div class="admin-panel"><div class="admin-table-wrap"><table class="admin-table" id="hist-table"><thead><tr><th>Faculty</th><th>Item</th><th>KRA / Indicator</th><th>Previous</th><th>Updated</th><th>Action</th><th>Remarks</th><th>When</th></tr></thead><tbody>' +
      body +
      '</tbody></table></div></div>'

    document.getElementById('hist-search').addEventListener('input', function (e) {
      var q = e.target.value.toLowerCase()
      document.querySelectorAll('#hist-table tbody tr').forEach(function (tr) {
        tr.style.display = tr.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none'
      })
    })
  })
}
