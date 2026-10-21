window.AdminPageInit = function (el) {
  var viewMonth = new Date(2026, 9, 1)
  var viewMode = 'month'
  var statusFilter = 'all'

  function fmtDate(d) {
    return d.toISOString().slice(0, 10)
  }

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
      var iso = fmtDate(new Date(year, month, day))
      var events = rows.filter(function (r) {
        return r.date === iso && r.status !== 'Cancelled'
      })
      cells.push(
        '<div class="sched-cal__cell"><span class="sched-cal__day">' +
          day +
          '</span>' +
          events
            .map(function (e) {
              return '<span class="sched-cal__event" title="' + e.faculty + '">' + e.time + ' ' + e.type + '</span>'
            })
            .join('') +
          '</div>'
      )
    }
    return cells.join('')
  }

  function renderTable(rows) {
    if (!rows.length) {
      return '<p class="admin-page-desc">No schedules match the current filter.</p>'
    }
    return (
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr>' +
      '<th>Date</th><th>Time</th><th>Type</th><th>Faculty</th><th>Reviewer</th><th>Status</th><th>Actions</th>' +
      '</tr></thead><tbody>' +
      rows
        .map(function (r) {
          return (
            '<tr data-sched-id="' +
            r.id +
            '"><td>' +
            r.date +
            '</td><td>' +
            r.time +
            '</td><td>' +
            r.type +
            '</td><td>' +
            r.faculty +
            '</td><td>' +
            r.reviewer +
            '</td><td>' +
            r.status +
            '</td><td class="sched-actions">' +
            '<button type="button" class="fl-btn fl-btn--ghost sched-view" data-id="' +
            r.id +
            '">View</button> ' +
            (r.status !== 'Cancelled'
              ? '<button type="button" class="fl-btn fl-btn--ghost sched-edit" data-id="' +
                r.id +
                '">Edit</button> ' +
                '<button type="button" class="fl-btn fl-btn--ghost sched-cancel" data-id="' +
                r.id +
                '">Cancel</button>'
              : '') +
            '</td></tr>'
          )
        })
        .join('') +
      '</tbody></table></div>'
    )
  }

  function openForm(mode, existing) {
    var row = existing || {}
    var html =
      '<form id="sched-form" class="sched-form">' +
      '<label>Academic year<input name="academicYear" required value="' +
      (row.academicYear || 'AY 2025–2026') +
      '" /></label>' +
      '<label>Semester<input name="semester" required value="' +
      (row.semester || '1st Semester') +
      '" /></label>' +
      '<label>Evaluation type<input name="type" required value="' +
      (row.type || '') +
      '" /></label>' +
      '<label>Faculty<input name="faculty" required value="' +
      (row.faculty || '') +
      '" /></label>' +
      '<label>Reviewer<input name="reviewer" required value="' +
      (row.reviewer || '') +
      '" /></label>' +
      '<label>Date<input name="date" type="date" required value="' +
      (row.date || '') +
      '" /></label>' +
      '<label>Time<input name="time" type="time" required value="' +
      (row.time || '09:00') +
      '" /></label>' +
      '<label>Location<input name="location" value="' +
      (row.location || '') +
      '" /></label>' +
      '<label>Notes<textarea name="notes" rows="3">' +
      (row.notes || '') +
      '</textarea></label>' +
      '<div class="sched-form__actions"><button type="submit" class="fl-btn fl-btn--primary">' +
      (mode === 'edit' ? 'Save Changes' : 'Add Schedule') +
      '</button></div></form>'

    var wrap = document.createElement('div')
    wrap.className = 'sched-modal'
    wrap.innerHTML =
      '<div class="sched-modal__backdrop"></div><div class="sched-modal__panel"><h3>' +
      (mode === 'edit' ? 'Edit Schedule' : 'Add Schedule') +
      '</h3>' +
      html +
      '</div>'
    document.body.appendChild(wrap)

    wrap.querySelector('.sched-modal__backdrop').addEventListener('click', function () {
      wrap.remove()
    })

    wrap.querySelector('#sched-form').addEventListener('submit', function (e) {
      e.preventDefault()
      var fd = new FormData(e.target)
      var payload = {
        academicYear: fd.get('academicYear'),
        semester: fd.get('semester'),
        type: fd.get('type'),
        faculty: fd.get('faculty'),
        facultyId: row.facultyId || 'F-001',
        reviewer: fd.get('reviewer'),
        reviewerId: row.reviewerId || 'R-01',
        date: fd.get('date'),
        time: fd.get('time'),
        location: fd.get('location'),
        notes: fd.get('notes'),
        status: row.status || 'Scheduled',
      }
      var done = function () {
        wrap.remove()
        paint()
      }
      if (mode === 'edit') {
        FacultyLinkAdminApi.updateEvaluationSchedule(row.id, payload).then(done)
      } else {
        FacultyLinkAdminApi.saveEvaluationSchedule(payload).then(done)
      }
    })
  }

  function paint() {
    FacultyLinkAdminApi.listEvaluationSchedule().then(function (rows) {
      var filtered = rows.filter(function (r) {
        return statusFilter === 'all' || r.status === statusFilter
      })
      var upcoming = filtered
        .filter(function (r) {
          return r.status !== 'Cancelled'
        })
        .sort(function (a, b) {
          return a.date.localeCompare(b.date)
        })
        .slice(0, 3)

      el.innerHTML =
        '<div class="sched-page-head"><div><h1 class="admin-page-title">Evaluation Schedule</h1>' +
        '<p class="admin-page-desc">Plan faculty evaluation sessions, assign reviewers, and track schedule status.</p></div>' +
        '<button type="button" class="fl-btn fl-btn--primary" id="sched-add">Add Schedule</button></div>' +
        '<div class="sched-toolbar">' +
        '<button type="button" class="fl-btn fl-btn--ghost" id="sched-today">Today</button>' +
        '<button type="button" class="fl-btn fl-btn--ghost" id="sched-prev">←</button>' +
        '<strong id="sched-month">' +
        monthLabel(viewMonth) +
        '</strong>' +
        '<button type="button" class="fl-btn fl-btn--ghost" id="sched-next">→</button>' +
        '<select id="sched-status-filter" class="sched-filter"><option value="all">All statuses</option>' +
        '<option value="Scheduled">Scheduled</option><option value="Pending">Pending</option><option value="Cancelled">Cancelled</option></select>' +
        '</div>' +
        '<div class="sched-layout">' +
        '<section class="admin-panel sched-calendar"><h2>Calendar</h2><div class="sched-cal">' +
        renderCalendar(filtered) +
        '</div></section>' +
        '<section class="admin-panel"><h2>Upcoming evaluations</h2><ul class="sched-upcoming">' +
        upcoming
          .map(function (u) {
            return '<li><strong>' + u.date + ' ' + u.time + '</strong> — ' + u.faculty + ' (' + u.type + ')</li>'
          })
          .join('') +
        '</ul></section></div>' +
        '<section class="admin-panel" style="margin-top:20px"><h2>Schedule list</h2>' +
        renderTable(filtered) +
        '</section>'

      document.getElementById('sched-status-filter').value = statusFilter
      document.getElementById('sched-add').addEventListener('click', function () {
        openForm('add')
      })
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
      document.getElementById('sched-status-filter').addEventListener('change', function (e) {
        statusFilter = e.target.value
        paint()
      })

      el.querySelectorAll('.sched-view').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var id = btn.getAttribute('data-id')
          var row = filtered.find(function (r) {
            return r.id === id
          })
          if (!row) return
          alert(
            row.id +
              '\n' +
              row.academicYear +
              ' · ' +
              row.semester +
              '\n' +
              row.type +
              '\nFaculty: ' +
              row.faculty +
              '\nReviewer: ' +
              row.reviewer +
              '\nWhen: ' +
              row.date +
              ' ' +
              row.time +
              '\nStatus: ' +
              row.status +
              (row.notes ? '\nNotes: ' + row.notes : '')
          )
        })
      })
      el.querySelectorAll('.sched-edit').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var id = btn.getAttribute('data-id')
          var row = filtered.find(function (r) {
            return r.id === id
          })
          if (row) openForm('edit', row)
        })
      })
      el.querySelectorAll('.sched-cancel').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var id = btn.getAttribute('data-id')
          if (confirm('Cancel this evaluation schedule?')) {
            FacultyLinkAdminApi.cancelEvaluationSchedule(id).then(paint)
          }
        })
      })
    })
  }

  paint()
}
