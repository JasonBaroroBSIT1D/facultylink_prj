window.AdminPageInit = function (el) {
  var store = FacultyLinkEvaluationPeriods
  var ui = FacultyLinkPeriodUI
  var editing = false
  var creating = false
  var selectedPeriodId = null
  var notice = ''

  function activePeriod() {
    var rows = store.list()
    if (selectedPeriodId) {
      return rows.find(function (p) {
        return p.id === selectedPeriodId
      })
    }
    return store.focus(rows)
  }

  function splitInstant(iso) {
    if (!iso || iso.length < 16) return { date: '', time: '08:00' }
    return { date: iso.slice(0, 10), time: iso.slice(11, 16) || '08:00' }
  }

  function cycleLabel(period) {
    if (!period) return ''
    return period.academicYear || period.name || '—'
  }

  function formValues(period) {
    var open = splitInstant(period && period.opensAt)
    var close = splitInstant(period && period.closesAt)
    return {
      academicYear: (period && period.academicYear) || '',
      semester: (period && period.semester) || '',
      openingDate: open.date,
      openingTime: open.time,
      closingDate: close.date,
      closingTime: close.time || '23:59',
      submissionEnabled: period ? period.submissionEnabled !== false : true,
      reviewEnabled: period ? period.reviewEnabled !== false : true,
    }
  }

  function field(label, name, value, type, readonly) {
    return (
      '<label class="ep-field">' +
      label +
      '<input name="' +
      name +
      '" type="' +
      (type || 'text') +
      '" value="' +
      ui.esc(value) +
      '"' +
      (readonly ? ' readonly' : '') +
      ' aria-describedby="error-' +
      name +
      '" /><span class="ep-error" id="error-' +
      name +
      '"></span></label>'
    )
  }

  function registerBlock(rows) {
    if (!rows.length) return ''
    var groups = { Upcoming: [], Open: [], Closed: [] }
    rows.forEach(function (p) {
      groups[store.status(p)].push(p)
    })
    function section(title, items) {
      if (!items.length) return ''
      return (
        '<div style="margin-top:16px"><h3 style="font-size:0.92rem;margin:0 0 8px">' +
        ui.esc(title) +
        '</h3><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Academic year</th><th>Semester</th><th>Window</th><th>Status</th><th>Submissions</th><th>Reviews</th><th></th></tr></thead><tbody>' +
        items
          .map(function (p) {
            return (
              '<tr><td>' +
              ui.esc(p.academicYear) +
              '</td><td>' +
              ui.esc(p.semester) +
              '</td><td>' +
              ui.format(p.opensAt) +
              ' – ' +
              ui.format(p.closesAt) +
              '</td><td>' +
              ui.badge(p) +
              '</td><td>' +
              (p.submissionEnabled ? 'Enabled' : 'Paused') +
              '</td><td>' +
              (p.reviewEnabled ? 'Enabled' : 'Paused') +
              '</td><td><button type="button" class="fl-btn fl-btn--ghost" style="padding:4px 10px;font-size:0.78rem" data-action="pick" data-id="' +
              ui.esc(p.id) +
              '">Manage</button></td></tr>'
            )
          })
          .join('') +
        '</tbody></table></div></div>'
      )
    }
    return (
      '<section class="admin-panel" style="margin-top:20px"><div class="admin-panel__head"><h2>All evaluation periods</h2>' +
      '<button type="button" class="fl-btn fl-btn--ghost" data-action="create-new">Create period</button></div><div class="admin-panel__body">' +
      section('Open', groups.Open) +
      section('Upcoming', groups.Upcoming) +
      section('Closed', groups.Closed) +
      '</div></section>'
    )
  }

  function paint() {
    var period = creating ? null : activePeriod()
    var state = period ? store.status(period) : null
    var values = formValues(period)

    var viewBlock = ''
    if (period && !editing && !creating) {
      viewBlock =
        '<dl class="ep-config-dl">' +
        '<div><dt>Evaluation cycle / academic year</dt><dd>' +
        ui.esc(cycleLabel(period)) +
        '</dd></div>' +
        '<div><dt>Semester</dt><dd>' +
        ui.esc(period.semester) +
        '</dd></div>' +
        '<div><dt>Opening</dt><dd>' +
        ui.format(period.opensAt) +
        '</dd></div>' +
        '<div><dt>Closing</dt><dd>' +
        ui.format(period.closesAt) +
        '</dd></div>' +
        '<div><dt>Evaluation status</dt><dd>' +
        ui.badge(period) +
        '</dd></div>' +
        '<div><dt>Faculty submissions</dt><dd>' +
        (period.submissionEnabled ? 'Enabled' : 'Paused') +
        '</dd></div>' +
        '<div><dt>Reviewer activities</dt><dd>' +
        (period.reviewEnabled ? 'Enabled' : 'Paused') +
        '</dd></div>' +
        '</dl>' +
        '<p class="ep-config-note">All dates and times are Asia/Manila (UTC+8).</p>' +
        '<div class="ep-config-actions">' +
        '<button type="button" class="fl-btn fl-btn--ghost" data-action="edit">Edit Schedule</button>' +
        (state === 'Open'
          ? ' <button type="button" class="fl-btn fl-btn--ghost" data-action="close-early" data-id="' +
            ui.esc(period.id) +
            '">Close Early</button>'
          : '') +
        '</div>'
    }

    var formBlock = ''
    if (!period || editing || creating) {
      formBlock =
        '<form id="schedule-form" class="ep-config-form" novalidate>' +
        '<p class="ep-form-note">Set when the faculty evaluation period opens and closes. Times use Asia/Manila (UTC+8).</p>' +
        field('Evaluation cycle / academic year', 'academicYear', values.academicYear, 'text', false) +
        field('Semester', 'semester', values.semester, 'text', false) +
        '<div class="ep-form-grid">' +
        field('Opening date', 'openingDate', values.openingDate, 'date', false) +
        field('Opening time', 'openingTime', values.openingTime, 'time', false) +
        '</div>' +
        '<p class="ep-error" id="error-opensAt" role="alert"></p>' +
        '<div class="ep-form-grid">' +
        field('Closing date', 'closingDate', values.closingDate, 'date', false) +
        field('Closing time', 'closingTime', values.closingTime, 'time', false) +
        '</div>' +
        '<p class="ep-error" id="error-closesAt" role="alert"></p>' +
        '<label class="ep-field"><input type="checkbox" name="submissionEnabled"' +
        (values.submissionEnabled ? ' checked' : '') +
        ' /> Faculty submissions enabled</label>' +
        '<label class="ep-field"><input type="checkbox" name="reviewEnabled"' +
        (values.reviewEnabled ? ' checked' : '') +
        ' /> Reviewer activities enabled</label>' +
        (period && editing
          ? '<p class="ep-status ep-status--' +
            (state || 'upcoming').toLowerCase() +
            '" style="margin:12px 0">Current status: ' +
            (state || 'Upcoming') +
            ' (recalculated when saved)</p>'
          : '') +
        '<p class="ep-error" id="form-error" role="alert"></p>' +
        '<div class="ep-config-actions">' +
        (period && editing
          ? '<button type="button" class="fl-btn fl-btn--ghost" data-action="cancel-edit">Cancel</button>'
          : creating
            ? '<button type="button" class="fl-btn fl-btn--ghost" data-action="cancel-edit">Cancel</button>'
            : '') +
        '<button type="submit" class="fl-btn fl-btn--primary">' +
        (creating ? 'Create evaluation period' : 'Save evaluation schedule') +
        '</button></div></form>'
    }

    var rows = store.list()
    el.innerHTML =
      '<div class="ep-page ep-page--config">' +
      '<h1 class="admin-page-title">Evaluation Schedule</h1>' +
      '<p class="admin-page-desc">Configure evaluation periods stored in PostgreSQL for Admin and Reviewer portals.</p>' +
      '<div role="status" class="ep-notice"' +
      (notice ? '' : ' hidden') +
      '>' +
      ui.esc(notice) +
      '</div>' +
      '<section class="admin-panel ep-config-card">' +
      '<div class="admin-panel__head"><h2>Evaluation Period Settings</h2></div>' +
      '<div class="admin-panel__body ep-config-card__body">' +
      viewBlock +
      formBlock +
      '</div></section>' +
      registerBlock(rows) +
      '<p class="ep-footnote">Schedules are saved to PostgreSQL and shared across Admin and Reviewer web sessions.</p></div>'

    var form = el.querySelector('#schedule-form')
    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault()
        onSubmit(form)
      })
    }
  }

  function clearErrors(form) {
    ;[el, form].forEach(function (root) {
      if (root && root.querySelectorAll) {
        root.querySelectorAll('.ep-error').forEach(function (node) {
          node.textContent = ''
        })
      }
    })
    if (form.querySelectorAll) {
      form.querySelectorAll('[aria-invalid]').forEach(function (node) {
        node.removeAttribute('aria-invalid')
      })
    }
  }

  function applyValidationErrors(form, errors) {
    Object.keys(errors).forEach(function (key) {
      var target =
        key === 'opensAt'
          ? '#error-opensAt'
          : key === 'closesAt'
            ? '#error-closesAt'
            : key === 'academicYear'
              ? '#error-academicYear'
              : '#error-' + key
      var node = el.querySelector(target)
      if (node) node.textContent = errors[key]
      var inputName =
        key === 'opensAt'
          ? 'openingDate'
          : key === 'closesAt'
            ? 'closingDate'
            : key
      var input = form.elements.namedItem(inputName)
      if (input) input.setAttribute('aria-invalid', 'true')
    })
  }

  function buildEntry(fd) {
    var academicYear = String(fd.get('academicYear') || '').trim()
    var semester = String(fd.get('semester') || '').trim()
    return {
      name: 'Faculty Evaluation — ' + academicYear,
      academicYear: academicYear,
      semester: semester,
      opensAt: fd.get('openingDate') + 'T' + fd.get('openingTime') + ':00+08:00',
      closesAt: fd.get('closingDate') + 'T' + fd.get('closingTime') + ':00+08:00',
      description: 'Faculty self-assessment and advisory rank simulation window.',
      submissionEnabled: fd.get('submissionEnabled') === 'on',
      reviewEnabled: fd.get('reviewEnabled') === 'on',
    }
  }

  function confirmReplace() {
    return new Promise(function (resolve) {
      var settled = false
      var dialog = ui.dialog(
        'Save evaluation schedule?',
        '<div class="ep-dialog__body"><p>Confirm the opening, closing, and activity settings for this evaluation period.</p>' +
          '<div class="ep-dialog__actions"><button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
          '<button type="button" class="fl-btn fl-btn--primary" id="confirm-replace">Save schedule</button></div></div>'
      )
      dialog.querySelector('#confirm-replace').addEventListener('click', function () {
        settled = true
        dialog.close()
        resolve(true)
      })
      dialog.addEventListener('close', function () {
        if (!settled) resolve(false)
      })
    })
  }

  function onSubmit(form) {
    clearErrors(form)
    var period = creating ? null : activePeriod()
    var fd = new FormData(form)
    var entry = buildEntry(fd)
    var validation = store.validate(entry, period && period.id, store.list())
    if (Object.keys(validation.errors).length) {
      applyValidationErrors(form, validation.errors)
      var first = form.querySelector('[aria-invalid="true"]')
      if (first) first.focus()
      return
    }

    function save(acknowledge) {
      var submit = form.querySelector('[type="submit"]')
      submit.disabled = true
      FacultyLinkAdminApi.saveEvaluationPeriod(entry, creating ? null : period && period.id, acknowledge)
        .then(function () {
          notice = creating ? 'Evaluation period created.' : 'Evaluation schedule updated.'
          editing = false
          creating = false
          paint()
        })
        .catch(function (error) {
          if (error.validation && error.validation.overlaps && error.validation.overlaps.length) {
            confirmReplace().then(function (ok) {
              if (ok) save(true)
              else submit.disabled = false
            })
            return
          }
          if (error.validation && error.validation.errors) {
            applyValidationErrors(form, error.validation.errors)
          } else {
            el.querySelector('#form-error').textContent = error.message
          }
          submit.disabled = false
        })
    }

    if ((period && editing) || creating) {
      confirmReplace().then(function (ok) {
        if (ok) save(validation.overlaps.length > 0)
        else form.querySelector('[type="submit"]').disabled = false
      })
    } else {
      save(validation.overlaps.length > 0)
    }
  }

  el.addEventListener('click', function (e) {
    var button = e.target.closest('[data-action]')
    if (!button) return
    var action = button.getAttribute('data-action')
    if (action === 'edit') {
      editing = true
      creating = false
      paint()
      var first = el.querySelector('#schedule-form input[name="academicYear"]')
      if (first) first.focus()
    }
    if (action === 'cancel-edit') {
      editing = false
      creating = false
      notice = ''
      paint()
    }
    if (action === 'create-new') {
      selectedPeriodId = null
      creating = true
      editing = false
      notice = ''
      paint()
    }
    if (action === 'pick') {
      selectedPeriodId = button.getAttribute('data-id')
      creating = false
      editing = false
      notice = ''
      paint()
    }
    if (action === 'close-early') {
      var periodId = button.getAttribute('data-id')
      var target = store.list().find(function (p) {
        return p.id === periodId
      })
      if (!target || store.status(target) !== 'Open') {
        notice = 'Only an open evaluation period can be closed early.'
        paint()
        return
      }
      var settled = false
      var dialog = ui.dialog(
        'Close evaluation period early?',
        '<div class="ep-dialog__body"><p>This will end the evaluation window immediately using the server closing time. Faculty submissions and reviewer activities for this period will follow the updated schedule.</p>' +
          '<div class="ep-dialog__actions"><button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
          '<button type="button" class="fl-btn fl-btn--primary" id="confirm-close-early">Close period now</button></div></div>'
      )
      dialog.querySelector('#confirm-close-early').addEventListener('click', function () {
        settled = true
        dialog.close()
        button.disabled = true
        FacultyLinkAdminApi.closeEvaluationPeriod(periodId)
          .then(function () {
            notice = 'Evaluation period closed early.'
            editing = false
            paint()
          })
          .catch(function (err) {
            notice = err.message || 'Unable to close evaluation period.'
            paint()
          })
      })
      dialog.addEventListener('close', function () {
        if (!settled) paint()
      })
    }
  })

  el.innerHTML = '<p class="ep-empty" role="status">Loading evaluation schedule…</p>'
  FacultyLinkAdminHttp.ensureCsrf()
    .then(function () {
      return FacultyLinkAdminApi.listEvaluationPeriods()
    })
    .then(function () {
      store.subscribe(paint)
      paint()
    })
    .catch(function () {
      el.innerHTML =
        '<p class="ep-empty" role="alert">Unable to load the evaluation schedule. Reload this page to try again.</p>'
    })
}
