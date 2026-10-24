window.AdminPageInit = function (el) {
  var store = FacultyLinkEvaluationPeriods
  var ui = FacultyLinkPeriodUI
  var notice = ''
  var loadError = ''
  var loading = true
  var modalMode = null
  var modalPeriodId = null

  function splitInstant(iso) {
    if (!iso || iso.length < 16) return { date: '', time: '08:00' }
    return { date: iso.slice(0, 10), time: iso.slice(11, 16) || '08:00' }
  }

  function summaryCounts(rows) {
    var counts = { Open: 0, Upcoming: 0, Closed: 0 }
    rows.forEach(function (p) {
      counts[store.status(p)] = (counts[store.status(p)] || 0) + 1
    })
    return counts
  }

  function field(label, name, value, type, opts) {
    opts = opts || {}
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
      (opts.required ? ' required' : '') +
      (opts.placeholder ? ' placeholder="' + ui.esc(opts.placeholder) + '"' : '') +
      ' aria-describedby="error-' +
      name +
      '" /><span class="ep-error" id="error-' +
      name +
      '"></span></label>'
    )
  }

  function toggleRow(name, label, helper, checked) {
    return (
      '<label class="ep-toggle-row">' +
      '<span class="ep-toggle-row__text"><strong>' +
      ui.esc(label) +
      '</strong><span>' +
      ui.esc(helper) +
      '</span></span>' +
      '<input type="checkbox" class="ep-toggle" name="' +
      name +
      '"' +
      (checked ? ' checked' : '') +
      ' role="switch" aria-checked="' +
      (checked ? 'true' : 'false') +
      '" /></label>'
    )
  }

  function formHtml(period) {
    var values = {
      periodName: (period && period.name) || '',
      academicYear: (period && period.academicYear) || '',
      semester: (period && period.semester) || '',
      openingDate: splitInstant(period && period.opensAt).date,
      openingTime: splitInstant(period && period.opensAt).time,
      closingDate: splitInstant(period && period.closesAt).date,
      closingTime: splitInstant(period && period.closesAt).time || '23:59',
      submissionEnabled: period ? period.submissionEnabled !== false : true,
      reviewEnabled: period ? period.reviewEnabled !== false : true,
    }
    return (
      '<form id="schedule-form" class="ep-config-form" novalidate>' +
      '<p class="ep-form-note">All times follow Philippine Standard Time (Asia/Manila, UTC+8).</p>' +
      '<fieldset class="ep-form-section"><legend>Period Information</legend>' +
      field('Evaluation cycle / Academic Year', 'academicYear', values.academicYear, 'text', {
        required: true,
        placeholder: 'e.g. 2025–2026',
      }) +
      field('Semester', 'semester', values.semester, 'text', { required: true, placeholder: 'e.g. First Semester' }) +
      field('Period Name', 'periodName', values.periodName, 'text', {
        placeholder: 'Optional display name for this evaluation period',
      }) +
      '</fieldset>' +
      '<fieldset class="ep-form-section"><legend>Schedule</legend>' +
      '<div class="ep-form-grid">' +
      field('Opening Date', 'openingDate', values.openingDate, 'date', { required: true }) +
      field('Opening Time', 'openingTime', values.openingTime, 'time', { required: true }) +
      '</div>' +
      '<p class="ep-error" id="error-opensAt" role="alert"></p>' +
      '<div class="ep-form-grid">' +
      field('Closing Date', 'closingDate', values.closingDate, 'date', { required: true }) +
      field('Closing Time', 'closingTime', values.closingTime, 'time', { required: true }) +
      '</div>' +
      '<p class="ep-error" id="error-closesAt" role="alert"></p></fieldset>' +
      '<fieldset class="ep-form-section"><legend>Access Settings</legend>' +
      toggleRow(
        'submissionEnabled',
        'Enable Faculty Submissions',
        'Allow faculty to upload evidence and complete self-assessment during this period.',
        values.submissionEnabled
      ) +
      toggleRow(
        'reviewEnabled',
        'Enable Reviewer Access',
        'Allow reviewers to verify submissions and perform review activities during this period.',
        values.reviewEnabled
      ) +
      '</fieldset>' +
      '<p class="ep-error" id="form-error" role="alert"></p>' +
      '<div class="ep-dialog__actions">' +
      '<button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
      '<button type="submit" class="fl-btn fl-btn--primary">' +
      (modalMode === 'create' ? 'Create Evaluation Period' : 'Save Changes') +
      '</button></div></form>'
    )
  }

  function periodTable(rows) {
    if (!rows.length) {
      return (
        '<div class="ep-empty">' +
        '<h3>No evaluation periods yet</h3>' +
        '<p>Create an evaluation period to set submission and review windows for faculty.</p>' +
        '<button type="button" class="fl-btn fl-btn--primary" data-action="create-new">+ Create Evaluation Period</button></div>'
      )
    }
    return (
      '<div class="ep-table-wrap"><table class="ep-table"><thead><tr>' +
      '<th>Period</th><th>Academic Year</th><th>Semester</th><th>Opens</th><th>Closes</th><th>Status</th><th>Submissions</th><th>Reviews</th><th></th>' +
      '</tr></thead><tbody>' +
      rows
        .map(function (p) {
          var state = store.status(p)
          return (
            '<tr><td><strong>' +
            ui.esc(p.name) +
            '</strong></td><td>' +
            ui.esc(p.academicYear) +
            '</td><td>' +
            ui.esc(p.semester) +
            '</td><td>' +
            ui.format(p.opensAt) +
            '</td><td>' +
            ui.format(p.closesAt) +
            '</td><td>' +
            ui.badge(p) +
            '</td><td>' +
            (p.submissionEnabled ? 'Enabled' : 'Disabled') +
            '</td><td>' +
            (p.reviewEnabled ? 'Enabled' : 'Disabled') +
            '</td><td><div class="ep-row-actions">' +
            ui.action('Edit', 'edit', p.id) +
            (state === 'Open' ? ui.action('Close Early', 'close-early', p.id) : '') +
            '</div></td></tr>'
          )
        })
        .join('') +
      '</tbody></table></div>'
    )
  }

  function paint() {
    if (loading) {
      el.innerHTML =
        '<div class="ep-page"><h1 class="admin-page-title">Evaluation Schedule</h1>' +
        '<p class="ep-empty" role="status">Loading evaluation periods…</p></div>'
      return
    }
    if (loadError) {
      el.innerHTML =
        '<div class="ep-page"><h1 class="admin-page-title">Evaluation Schedule</h1>' +
        '<p class="ep-empty" role="alert">' +
        ui.esc(loadError) +
        '</p><button type="button" class="fl-btn fl-btn--primary" id="ep-reload">Try again</button></div>'
      var reload = document.getElementById('ep-reload')
      if (reload) reload.addEventListener('click', bootstrap)
      return
    }

    var rows = store.list()
    var counts = summaryCounts(rows)

    el.innerHTML =
      '<div class="ep-page">' +
      '<div class="ep-page-head">' +
      '<div><h1 class="admin-page-title">Evaluation Schedule</h1>' +
      '<p>Manage faculty evaluation periods, submission deadlines, and review schedules.</p></div>' +
      '<button type="button" class="fl-btn fl-btn--primary" data-action="create-new">+ Create Evaluation Period</button></div>' +
      (notice ? '<div role="status" class="ep-notice">' + ui.esc(notice) + '</div>' : '') +
      '<div class="ep-summary ep-summary--dashboard">' +
      '<article><span>Active Periods</span><strong>' +
      counts.Open +
      '</strong><small>Currently open</small></article>' +
      '<article><span>Upcoming Periods</span><strong>' +
      counts.Upcoming +
      '</strong><small>Scheduled to open</small></article>' +
      '<article><span>Completed Periods</span><strong>' +
      counts.Closed +
      '</strong><small>Closed windows</small></article>' +
      '</div>' +
      '<section class="ep-register">' +
      '<div class="ep-section-head"><div><h2>Evaluation Periods</h2><p>Stored in PostgreSQL and shared with Reviewer and Faculty apps.</p></div>' +
      '<span class="ep-zone">Asia/Manila (UTC+8)</span></div>' +
      periodTable(rows) +
      '</section></div>'
  }

  function openModal(mode, period) {
    modalMode = mode
    modalPeriodId = period ? period.id : null
    var title = mode === 'create' ? 'Create Evaluation Period' : 'Edit Evaluation Period'
    var dialog = ui.dialog(title, '<div class="ep-dialog__body">' + formHtml(period) + '</div>')
    var form = dialog.querySelector('#schedule-form')
    form.addEventListener('submit', function (e) {
      e.preventDefault()
      onSubmit(form, dialog)
    })
  }

  function clearErrors(form, root) {
    ;[root, form].forEach(function (node) {
      if (!node || !node.querySelectorAll) return
      node.querySelectorAll('.ep-error').forEach(function (n) {
        n.textContent = ''
      })
    })
    form.querySelectorAll('[aria-invalid]').forEach(function (n) {
      n.removeAttribute('aria-invalid')
    })
  }

  function applyValidationErrors(form, root, errors) {
    Object.keys(errors).forEach(function (key) {
      var target =
        key === 'opensAt'
          ? '#error-opensAt'
          : key === 'closesAt'
            ? '#error-closesAt'
            : '#error-' + key
      var node = root.querySelector(target)
      if (node) node.textContent = errors[key]
      var inputName =
        key === 'opensAt' ? 'openingDate' : key === 'closesAt' ? 'closingDate' : key === 'name' ? 'periodName' : key
      var input = form.elements.namedItem(inputName)
      if (input) input.setAttribute('aria-invalid', 'true')
    })
  }

  function buildEntry(fd) {
    var academicYear = String(fd.get('academicYear') || '').trim()
    var periodName = String(fd.get('periodName') || '').trim()
    return {
      name: periodName || 'Faculty Evaluation — ' + academicYear,
      academicYear: academicYear,
      semester: String(fd.get('semester') || '').trim(),
      opensAt: fd.get('openingDate') + 'T' + fd.get('openingTime') + ':00+08:00',
      closesAt: fd.get('closingDate') + 'T' + fd.get('closingTime') + ':00+08:00',
      description: 'Faculty self-assessment and advisory rank simulation window.',
      submissionEnabled: fd.get('submissionEnabled') === 'on',
      reviewEnabled: fd.get('reviewEnabled') === 'on',
    }
  }

  function confirmSave(isCreate) {
    return new Promise(function (resolve) {
      var settled = false
      var dialog = ui.dialog(
        isCreate ? 'Create evaluation period?' : 'Save changes?',
        '<div class="ep-dialog__body"><p>Confirm the schedule and access settings for this evaluation period.</p>' +
          '<div class="ep-dialog__actions"><button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
          '<button type="button" class="fl-btn fl-btn--primary" id="confirm-save">Confirm</button></div></div>'
      )
      dialog.querySelector('#confirm-save').addEventListener('click', function () {
        settled = true
        dialog.close()
        resolve(true)
      })
      dialog.addEventListener('close', function () {
        if (!settled) resolve(false)
      })
    })
  }

  function confirmOverlap(overlaps) {
    var list =
      overlaps && overlaps.length
        ? '<ul class="ep-overlap-list">' +
          overlaps
            .map(function (p) {
              return (
                '<li><strong>' +
                ui.esc(p.name || 'Period') +
                '</strong> — ' +
                ui.esc(p.academicYear || '') +
                ' · opens ' +
                ui.format(p.opensAt) +
                ', closes ' +
                ui.format(p.closesAt) +
                '</li>'
              )
            })
            .join('') +
          '</ul>'
        : ''
    return new Promise(function (resolve) {
      var settled = false
      var dialog = ui.dialog(
        'Overlapping evaluation window',
        '<div class="ep-dialog__body"><p>This schedule overlaps one or more existing periods. You can continue only if overlapping windows are intentional.</p>' +
          list +
          '<div class="ep-dialog__actions"><button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
          '<button type="button" class="fl-btn fl-btn--primary" id="confirm-overlap">Save anyway</button></div></div>'
      )
      dialog.querySelector('#confirm-overlap').addEventListener('click', function () {
        settled = true
        dialog.close()
        resolve(true)
      })
      dialog.addEventListener('close', function () {
        if (!settled) resolve(false)
      })
    })
  }

  function resetSubmitButton(submit) {
    submit.disabled = false
    submit.textContent = modalMode === 'create' ? 'Create Evaluation Period' : 'Save Changes'
  }

  function onSubmit(form, dialog) {
    clearErrors(form, dialog)
    var period =
      modalMode === 'edit'
        ? store.list().find(function (p) {
            return p.id === modalPeriodId
          })
        : null
    var fd = new FormData(form)
    var entry = buildEntry(fd)
    var validation = store.validate(entry, period && period.id, store.list())
    if (Object.keys(validation.errors).length) {
      applyValidationErrors(form, dialog, validation.errors)
      var first = form.querySelector('[aria-invalid="true"]')
      if (first) first.focus()
      return
    }

    confirmSave(modalMode === 'create').then(function (ok) {
      if (!ok) return
      var submit = form.querySelector('[type="submit"]')
      var periodId = modalMode === 'create' ? null : period && period.id

      function persist(acknowledgeOverlap) {
        submit.disabled = true
        submit.textContent = modalMode === 'create' ? 'Creating period...' : 'Saving...'
        return FacultyLinkAdminApi.saveEvaluationPeriod(entry, periodId, acknowledgeOverlap)
          .then(function () {
            notice = modalMode === 'create' ? 'Evaluation period created.' : 'Evaluation schedule updated.'
            modalMode = null
            dialog.close()
            paint()
          })
          .catch(function (error) {
            var overlaps = error.validation && error.validation.overlaps
            if (overlaps && overlaps.length && !acknowledgeOverlap) {
              confirmOverlap(overlaps).then(function (retry) {
                if (!retry) {
                  resetSubmitButton(submit)
                  return
                }
                persist(true)
              })
              return
            }
            if (error.validation && error.validation.errors) {
              applyValidationErrors(form, dialog, error.validation.errors)
            } else {
              dialog.querySelector('#form-error').textContent = error.message
            }
            resetSubmitButton(submit)
          })
      }

      persist(false)
    })
  }

  function closeEarly(periodId) {
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
      '<div class="ep-dialog__body"><p>This ends the evaluation window immediately using the server closing time.</p>' +
        '<div class="ep-dialog__actions"><button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
        '<button type="button" class="fl-btn fl-btn--primary" id="confirm-close-early">Close period now</button></div></div>'
    )
    dialog.querySelector('#confirm-close-early').addEventListener('click', function () {
      settled = true
      dialog.close()
      FacultyLinkAdminApi.closeEvaluationPeriod(periodId)
        .then(function () {
          notice = 'Evaluation period closed early.'
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

  el.addEventListener('click', function (e) {
    var button = e.target.closest('[data-action]')
    if (!button) return
    var action = button.getAttribute('data-action')
    if (action === 'create-new') {
      notice = ''
      openModal('create', null)
    }
    if (action === 'edit') {
      var id = button.getAttribute('data-id')
      var period = store.list().find(function (p) {
        return p.id === id
      })
      if (period) openModal('edit', period)
    }
    if (action === 'close-early') closeEarly(button.getAttribute('data-id'))
  })

  function bootstrap() {
    loading = true
    loadError = ''
    paint()
    FacultyLinkAdminHttp.ensureCsrf()
      .then(function () {
        return FacultyLinkAdminApi.listEvaluationPeriods()
      })
      .then(function () {
        loading = false
        store.subscribe(paint)
        paint()
        ui.watch(paint)
      })
      .catch(function (err) {
        loading = false
        loadError = err.message || 'Unable to load the evaluation schedule.'
        paint()
      })
  }

  bootstrap()
}
