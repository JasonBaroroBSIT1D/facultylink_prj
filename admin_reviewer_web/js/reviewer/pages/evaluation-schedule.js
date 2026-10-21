window.ReviewerPageInit = function (el) {
  var viewMonth = new Date(2026, 9, 1)

  function monthLabel(d) {
    return d.toLocaleString('en-US', { month: 'long', year: 'numeric' })
  }

  function renderCalendar(rows) {
    var year = viewMonth.getFullYear()
    var month = viewMonth.getMonth()
    var first = new Date(year, month, 1)
    var startDay = first.getDay()
    var daysInMonth = new Date(year, month + 1, 0).getDate()
    var cells = []
    for (var i = 0; i < startDay; i++) cells.push('<div class="sched-cal__cell sched-cal__cell--muted"></div>')
    for (var day = 1; day <= daysInMonth; day++) {
      var iso = new Date(year, month, day).toISOString().slice(0, 10)
      var events = rows.filter(function (r) {
        return r.date === iso
      })
      cells.push(
        '<div class="sched-cal__cell"><span class="sched-cal__day">' +
          day +
          '</span>' +
          events
            .map(function (e) {
              return '<span class="sched-cal__event">' + e.time + ' ' + e.faculty + '</span>'
            })
            .join('') +
          '</div>'
      )
    }
    return cells.join('')
  }

  function paint() {
    FacultyLinkReviewerApi.listEvaluationSchedule().then(function (rows) {
      var upcoming = rows.slice().sort(function (a, b) {
        return a.date.localeCompare(b.date)
      })

      el.innerHTML =
        '<h1 class="admin-page-title">Evaluation Schedule</h1>' +
        '<p class="admin-page-desc">View assigned evaluation sessions and open related faculty assessments.</p>' +
        '<div class="sched-toolbar">' +
        '<button type="button" class="fl-btn fl-btn--ghost" id="sched-today">Today</button>' +
        '<button type="button" class="fl-btn fl-btn--ghost" id="sched-prev">←</button>' +
        '<strong id="sched-month">' +
        monthLabel(viewMonth) +
        '</strong>' +
        '<button type="button" class="fl-btn fl-btn--ghost" id="sched-next">→</button>' +
        '</div>' +
        '<div class="sched-layout">' +
        '<section class="admin-panel sched-calendar"><h2>Assigned calendar</h2><div class="sched-cal">' +
        renderCalendar(rows) +
        '</div></section>' +
        '<section class="admin-panel"><h2>Upcoming</h2><ul class="sched-upcoming">' +
        upcoming
          .map(function (u) {
            return (
              '<li><strong>' +
              u.date +
              ' ' +
              u.time +
              '</strong> — ' +
              u.faculty +
              ' · ' +
              u.type +
              ' <span class="admin-sample-tag inline">Sample Data</span></li>'
            )
          })
          .join('') +
        '</ul></section></div>' +
        '<section class="admin-panel" style="margin-top:20px"><h2>Schedule details</h2>' +
        '<div class="admin-table-wrap"><table class="admin-table"><thead><tr>' +
        '<th>Date</th><th>Time</th><th>Type</th><th>Faculty</th><th>Status</th><th>Actions</th>' +
        '</tr></thead><tbody>' +
        rows
          .map(function (r) {
            return (
              '<tr><td>' +
              r.date +
              '</td><td>' +
              r.time +
              '</td><td>' +
              r.type +
              '</td><td>' +
              r.faculty +
              '</td><td>' +
              r.status +
              '</td><td>' +
              '<button type="button" class="fl-btn fl-btn--ghost sched-view" data-id="' +
              r.id +
              '">View Details</button> ' +
              '<a class="fl-btn fl-btn--ghost" href="kra-assessment.html?faculty=' +
              encodeURIComponent(r.facultyId || 'F-001') +
              '">Open Assessment</a>' +
              '</td></tr>'
            )
          })
          .join('') +
        '</tbody></table></div></section>'

      document.getElementById('sched-today').addEventListener('click', function () {
        viewMonth = new Date()
        paint()
      })
      document.getElementById('sched-prev').addEventListener('click', function () {
        viewMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() - 1, 1)
        paint()
      })
      document.getElementById('sched-next').addEventListener('click', function () {
        viewMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1)
        paint()
      })

      el.querySelectorAll('.sched-view').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var id = btn.getAttribute('data-id')
          var row = rows.find(function (r) {
            return r.id === id
          })
          if (!row) return
          alert(
            row.type +
              '\n' +
              row.academicYear +
              ' · ' +
              row.semester +
              '\nFaculty: ' +
              row.faculty +
              '\nWhen: ' +
              row.date +
              ' ' +
              row.time +
              '\nLocation: ' +
              (row.location || '—') +
              '\nStatus: ' +
              row.status
          )
        })
      })
    })
  }

  paint()
}
