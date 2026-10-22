window.ReviewerPageInit = function (el, h) {
  var state = { rows: [], filter: '', loading: true, error: '' }

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    })
  }

  function paintTable(rows) {
    if (!rows.length) {
      return '<p class="admin-page-desc">No faculty members are assigned to you yet.</p>'
    }
    return (
      '<div class="admin-table-wrap"><table class="admin-table" id="faculty-table"><thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Rank</th><th>Status</th><th>Docs</th><th></th></tr></thead><tbody>' +
      rows
        .map(function (f) {
          return (
            '<tr><td>' +
            esc(f.faculty_id) +
            '</td><td><strong>' +
            esc(f.name) +
            '</strong><br /><span style="font-size:0.78rem;color:var(--fl-text-muted)">' +
            esc(f.email) +
            '</span></td><td>' +
            esc(f.department) +
            '</td><td>' +
            esc(f.rank) +
            '</td><td>' +
            h.statusBadge(f.status) +
            '</td><td>' +
            esc(f.documents) +
            '</td><td><a class="fl-btn fl-btn--primary" style="padding:6px 14px;font-size:0.8rem" href="faculty-overview.html?id=' +
            encodeURIComponent(f.faculty_id) +
            '">View Assessment</a></td></tr>'
          )
        })
        .join('') +
      '</tbody></table></div>'
    )
  }

  function paint() {
    el.innerHTML =
      '<h1 class="admin-page-title">Assigned Faculty</h1>' +
      '<p class="admin-page-desc">Faculty assigned to you for document verification and KRA assessment support.</p>' +
      (state.error ? '<p class="ep-notice" role="alert">' + esc(state.error) + '</p>' : '') +
      '<div class="admin-filter-bar"><input type="search" id="faculty-filter" placeholder="Filter by name, email, department…" value="' +
      esc(state.filter) +
      '" /><select disabled><option>All departments</option></select></div>' +
      '<div class="admin-panel">' +
      (state.loading ? '<p class="admin-page-desc">Loading assigned faculty…</p>' : paintTable(state.rows)) +
      '</div>'

    var search = document.getElementById('faculty-filter')
    if (search) {
      search.addEventListener('input', function (e) {
        state.filter = e.target.value
        load()
      })
    }
  }

  function load() {
    state.loading = true
    state.error = ''
    paint()
    FacultyLinkReviewerHttp.ensureCsrf()
      .then(function () {
        return FacultyLinkReviewerApi.listAssignedFaculty(state.filter)
      })
      .then(function (rows) {
        state.rows = rows
        state.loading = false
        paint()
      })
      .catch(function (err) {
        state.loading = false
        state.error = err.message || 'Unable to load assigned faculty.'
        paint()
      })
  }

  load()
}
