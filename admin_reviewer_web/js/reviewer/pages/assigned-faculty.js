window.ReviewerPageInit = function (el, h) {
  var state = { allRows: [], filter: '', department: '', loading: true, error: '', forbidden: false }

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    })
  }

  function formatDepartment(value) {
    if (!value || value === '—' || value === '-') return 'Not specified'
    return value
  }

  function departmentsFrom(rows) {
    var set = {}
    rows.forEach(function (f) {
      var d = formatDepartment(f.department)
      if (d !== 'Not specified') set[d] = true
    })
    return Object.keys(set).sort()
  }

  function filteredRows() {
    var q = state.filter.trim().toLowerCase()
    return state.allRows.filter(function (f) {
      var dept = formatDepartment(f.department)
      if (state.department && dept !== state.department) return false
      if (!q) return true
      var blob = [f.name, f.email, dept, f.rank, f.employee_number || ''].join(' ').toLowerCase()
      return blob.indexOf(q) >= 0
    })
  }

  function paintTable(rows) {
    if (!rows.length) {
      if (state.allRows.length && (state.filter || state.department)) {
        return (
          '<div class="ep-empty ep-empty--compact"><h3>No matches</h3>' +
          '<p>Try adjusting your search or department filter.</p></div>'
        )
      }
      return (
        '<div class="ep-empty ep-empty--compact"><h3>No faculty assigned yet</h3>' +
        '<p>When an administrator assigns faculty to you, they will appear here.</p></div>'
      )
    }
    return (
      '<div class="admin-table-wrap"><table class="admin-table" id="faculty-table"><thead><tr>' +
      '<th>Name</th><th>Department</th><th>Rank</th><th>Status</th><th>Documents</th><th></th>' +
      '</tr></thead><tbody>' +
      rows
        .map(function (f) {
          return (
            '<tr><td><strong>' +
            esc(f.name) +
            '</strong><br /><span class="admin-person-cell__email">' +
            esc(f.email) +
            '</span></td><td>' +
            esc(formatDepartment(f.department)) +
            '</td><td>' +
            esc(f.rank && f.rank !== '—' ? f.rank : 'Not specified') +
            '</td><td>' +
            h.statusBadge(f.status) +
            '</td><td>' +
            esc(String(f.documents)) +
            '</td><td><a class="fl-btn fl-btn--primary fl-btn--sm" href="faculty-overview.html?id=' +
            encodeURIComponent(f.faculty_id) +
            '">View</a></td></tr>'
          )
        })
        .join('') +
      '</tbody></table></div>'
    )
  }

  function departmentOptions(rows) {
    var opts = '<option value="">All departments</option>'
    departmentsFrom(rows).forEach(function (d) {
      opts +=
        '<option value="' +
        esc(d) +
        '"' +
        (state.department === d ? ' selected' : '') +
        '>' +
        esc(d) +
        '</option>'
    })
    return opts
  }

  function paint() {
    var rows = filteredRows()
    el.innerHTML =
      '<div class="ep-page">' +
      '<h1 class="admin-page-title">Assigned Faculty</h1>' +
      '<p class="admin-page-desc">Faculty assigned to you for document verification and KRA assessment.</p>' +
      (state.forbidden
        ? '<p class="ep-notice" role="alert">Your session cannot access assigned faculty. Sign in again as a reviewer.</p>'
        : state.error
          ? '<p class="ep-notice" role="alert">' + esc(state.error) + '</p>'
          : '') +
      '<div class="admin-filter-bar">' +
      '<input type="search" id="faculty-filter" placeholder="Search by name, email, or department…" value="' +
      esc(state.filter) +
      '" aria-label="Search assigned faculty" />' +
      '<select id="faculty-dept-filter" aria-label="Filter by department">' +
      departmentOptions(state.allRows) +
      '</select>' +
      '<button type="button" class="fl-btn fl-btn--ghost" id="faculty-refresh">Refresh</button>' +
      '</div>' +
      '<div class="admin-panel">' +
      (state.loading
        ? '<p class="admin-page-desc" role="status">Loading assigned faculty…</p>'
        : paintTable(rows)) +
      '</div></div>'

    var search = document.getElementById('faculty-filter')
    if (search) {
      search.addEventListener('input', function (e) {
        state.filter = e.target.value
        paint()
      })
    }
    var dept = document.getElementById('faculty-dept-filter')
    if (dept) {
      dept.addEventListener('change', function (e) {
        state.department = e.target.value
        paint()
      })
    }
    var refresh = document.getElementById('faculty-refresh')
    if (refresh) refresh.addEventListener('click', loadFromServer)
  }

  function loadFromServer() {
    state.loading = true
    state.error = ''
    state.forbidden = false
    paint()
    FacultyLinkReviewerHttp.ensureCsrf()
      .then(function () {
        return FacultyLinkReviewerApi.listAssignedFaculty('')
      })
      .then(function (rows) {
        state.allRows = rows
        state.loading = false
        paint()
      })
      .catch(function (err) {
        state.loading = false
        state.error = err.message || 'Unable to load assigned faculty.'
        if (/access|forbidden|authentication/i.test(state.error)) state.forbidden = true
        paint()
      })
  }

  loadFromServer()
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') loadFromServer()
  })
}
