window.ReviewerPageInit = function (el, h) {
  FacultyLinkReviewerApi.listDocuments().then(function (docs) {
    function renderRows(list) {
      return list
        .map(function (d) {
          return (
            '<tr data-row><td>' +
            d.id +
            '</td><td>' +
            d.faculty +
            '</td><td>' +
            d.title +
            '</td><td>' +
            d.kra +
            ' / ' +
            d.criterion +
            ' / ' +
            d.indicator +
            '</td><td>' +
            d.uploaded +
            '</td><td>' +
            h.statusBadge(d.reviewStatus) +
            '</td><td><a href="document-detail.html?id=' +
            encodeURIComponent(d.id) +
            '">View Document</a></td></tr>'
          )
        })
        .join('')
    }

    el.innerHTML =
      '<h1 class="admin-page-title">Document Review</h1>' +
      '<p class="admin-page-desc">Review queue with OCR, rule-based validation, and authorized decisions. System Approved documents passed all mandatory rules.</p>' +
      '<div class="admin-filter-bar">' +
      '<input type="search" id="doc-search" placeholder="Search…" />' +
      '<select id="doc-status-filter"><option value="">All statuses</option><option>System Approved</option><option>Needs Verification</option><option>Needs Revision</option><option>Rejected</option></select>' +
      '</div>' +
      '<div class="admin-panel"><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Faculty</th><th>Title</th><th>KRA / Criterion / Indicator</th><th>Uploaded</th><th>Review status</th><th></th></tr></thead><tbody id="doc-tbody">' +
      renderRows(docs) +
      '</tbody></table></div></div>'

    function applyFilters() {
      var q = document.getElementById('doc-search').value.toLowerCase()
      var st = document.getElementById('doc-status-filter').value
      document.querySelectorAll('#doc-tbody tr').forEach(function (tr) {
        var text = tr.textContent
        var ok = text.toLowerCase().indexOf(q) >= 0 && (!st || text.indexOf(st) >= 0)
        tr.style.display = ok ? '' : 'none'
      })
    }
    document.getElementById('doc-search').addEventListener('input', applyFilters)
    document.getElementById('doc-status-filter').addEventListener('change', applyFilters)
  })
}
