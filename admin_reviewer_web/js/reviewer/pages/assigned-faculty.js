window.ReviewerPageInit = function (el, h) {
  FacultyLinkReviewerApi.listAssignedFaculty().then(function (rows) {
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
          h.statusBadge(f.status) +
          '</td><td>' +
          f.documents +
          '</td><td><a class="fl-btn fl-btn--primary" style="padding:6px 14px;font-size:0.8rem" href="faculty-overview.html?id=' +
          encodeURIComponent(f.id) +
          '">View Assessment</a></td></tr>'
        )
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Assigned Faculty</h1>' +
      '<p class="admin-page-desc">Faculty assigned to you for document verification and KRA assessment support.</p>' +
      '<div class="admin-filter-bar"><input type="search" id="faculty-filter" placeholder="Filter by name…" /><select disabled><option>All departments (mock)</option></select></div>' +
      '<div class="admin-panel"><div class="admin-table-wrap"><table class="admin-table" id="faculty-table"><thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Rank</th><th>Status</th><th>Docs</th><th></th></tr></thead><tbody>' +
      body +
      '</tbody></table></div></div>'

    document.getElementById('faculty-filter').addEventListener('input', function (e) {
      var q = e.target.value.toLowerCase()
      document.querySelectorAll('#faculty-table tbody tr').forEach(function (tr) {
        tr.style.display = tr.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none'
      })
    })
  })
}
