window.AdminPageInit = function (el) {
  var ui = window.FacultyLinkAdminAccountUi || {
    esc: function (v) {
      return String(v == null ? '' : v)
    },
  }

  var THRESHOLD_LABELS = {
    classification_min: 'Classification confidence minimum',
    field_min: 'Required field confidence minimum',
    identity_min: 'Faculty identity match minimum',
    ocr_mean_min: 'Overall OCR confidence minimum',
  }

  var state = { operational: null, editing: false, draft: {}, message: null, loading: true, error: '' }

  function renderLockedOfficial(locked) {
    if (!locked) return ''
    return (
      '<ul class="kra-operational-locked">' +
      '<li><strong>Reference scoring (locked on KRA Configuration):</strong></li>' +
      '<li>Criterion A maximum: ' +
      ui.esc(locked.criterion_max_points) +
      ' points</li>' +
      '<li>SET maximum: ' +
      ui.esc(locked.set_max_points) +
      ' · ' +
      ui.esc(locked.set_formula) +
      '</li>' +
      '<li>SEF maximum: ' +
      ui.esc(locked.sef_max_points) +
      ' · ' +
      ui.esc(locked.sef_formula) +
      '</li></ul>'
    )
  }

  function renderOperationalSection() {
    var op = state.operational
    if (!op) {
      return (
        '<div class="admin-panel"><p class="admin-page-desc">KRA I Criterion A is not configured in PostgreSQL. Import or seed SET/SEF before editing validation thresholds.</p></div>'
      )
    }

    var thresholds = state.editing ? state.draft : op.confidence_thresholds || {}
    var bounds = op.confidence_threshold_bounds || {}
    var keys = Object.keys(THRESHOLD_LABELS)

    var fieldsHtml = keys
      .map(function (key) {
        var b = bounds[key] || { min: 0, max: 1 }
        var val = thresholds[key] != null ? thresholds[key] : ''
        if (state.editing) {
          return (
            '<label><span>' +
            ui.esc(THRESHOLD_LABELS[key]) +
            '</span><input type="number" step="0.01" min="' +
            b.min +
            '" max="' +
            b.max +
            '" name="threshold_' +
            key +
            '" value="' +
            ui.esc(val) +
            '" required /></label>'
          )
        }
        return (
          '<p class="kra-muted"><strong>' +
          ui.esc(THRESHOLD_LABELS[key]) +
          ':</strong> ' +
          ui.esc(val) +
          '</p>'
        )
      })
      .join('')

    var notice = state.message
      ? '<p class="' +
        (state.message.type === 'error' ? 'admin-form-error' : 'ep-notice') +
        '" role="status">' +
        ui.esc(state.message.text) +
        '</p>'
      : ''

    var actions = state.editing
      ? '<div class="kra-operational-actions"><button type="button" class="fl-btn fl-btn--primary" data-vs-save>Save changes</button>' +
        '<button type="button" class="fl-btn fl-btn--ghost" data-vs-cancel>Cancel</button></div>'
      : '<div class="kra-operational-actions"><button type="button" class="fl-btn fl-btn--primary" data-vs-edit>Edit thresholds</button></div>'

    return (
      '<div class="admin-panel">' +
      '<div class="admin-panel__head"><h2>KRA I Criterion A — SET/SEF validation thresholds</h2></div>' +
      '<p class="admin-page-desc">Operational OCR confidence thresholds for the Phase 2.1 rule engine. Identity checks, duplicate protection, and evidence validation remain mandatory.</p>' +
      renderLockedOfficial(op.locked_official) +
      notice +
      (state.editing ? '<div class="kra-operational-form">' + fieldsHtml + '</div>' : '<div>' + fieldsHtml + '</div>') +
      actions +
      '</div>'
    )
  }

  function bindEvents() {
    var editBtn = el.querySelector('[data-vs-edit]')
    if (editBtn) {
      editBtn.addEventListener('click', function () {
        state.editing = true
        state.message = null
        state.draft = Object.assign({}, (state.operational && state.operational.confidence_thresholds) || {})
        paint()
      })
    }
    var cancelBtn = el.querySelector('[data-vs-cancel]')
    if (cancelBtn) {
      cancelBtn.addEventListener('click', function () {
        state.editing = false
        state.message = null
        paint()
      })
    }
    var saveBtn = el.querySelector('[data-vs-save]')
    if (saveBtn) {
      saveBtn.addEventListener('click', function () {
        state.message = null
        var payload = {}
        var invalid = false
        Object.keys(THRESHOLD_LABELS).forEach(function (key) {
          var input = el.querySelector('[name="threshold_' + key + '"]')
          if (!input) return
          var num = Number(input.value)
          if (Number.isNaN(num)) invalid = true
          else payload[key] = num
        })
        if (invalid) {
          state.message = { type: 'error', text: 'Enter valid threshold values.' }
          paint()
          return
        }
        if (
          !window.confirm(
            'Save updated OCR confidence thresholds for KRA I Criterion A (SET/SEF)? Scoring limits will not change.'
          )
        ) {
          return
        }
        saveBtn.disabled = true
        FacultyLinkAdminHttp.ensureCsrf()
          .then(function () {
            return FacultyLinkAdminApi.updateValidationScoringOperationalSettings(payload)
          })
          .then(function (body) {
            state.operational = body.operational || state.operational
            state.editing = false
            state.message = { type: 'success', text: 'Validation thresholds saved.' }
            paint()
          })
          .catch(function (err) {
            state.message = { type: 'error', text: err.message || 'Unable to save.' }
            paint()
          })
          .finally(function () {
            saveBtn.disabled = false
          })
      })
    }
    var retry = el.querySelector('[data-vs-retry]')
    if (retry) retry.addEventListener('click', load)
  }

  function paint() {
    if (state.loading) {
      el.innerHTML =
        '<h1 class="admin-page-title">Rule-Based Validation &amp; Scoring</h1>' +
        ui.loadingState('Loading validation settings…')
      return
    }
    if (state.error && !state.operational) {
      el.innerHTML =
        '<h1 class="admin-page-title">Rule-Based Validation &amp; Scoring</h1>' +
        '<div class="admin-error-state"><p>' +
        ui.esc(state.error) +
        '</p><button type="button" class="fl-btn fl-btn--primary" data-vs-retry>Try again</button></div>'
      bindEvents()
      return
    }

    el.innerHTML =
      '<h1 class="admin-page-title">Rule-Based Validation &amp; Scoring</h1>' +
      '<p class="admin-page-desc">Configure operational validation for document processing. Official KRA scoring rules are managed on the KRA Configuration page.</p>' +
      renderOperationalSection() +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Workflow status</h2></div>' +
      '<p class="admin-page-desc">Automatic scoring and system approval remain disabled (Pre-Phase 3). Documents continue to route to <strong>needs verification</strong> after OCR validation.</p></div>'

    bindEvents()
  }

  function load() {
    state.loading = true
    state.error = ''
    paint()
    FacultyLinkAdminHttp.ensureCsrf()
      .then(function () {
        return FacultyLinkAdminApi.getValidationScoringCriterionA()
      })
      .then(function (body) {
        state.operational = body.operational
        state.loading = false
      })
      .catch(function (err) {
        state.loading = false
        if (err.message && err.message.indexOf('not configured') >= 0) {
          state.operational = null
          state.error = ''
        } else {
          state.error = err.message || 'Unable to load validation settings.'
        }
      })
      .finally(function () {
        paint()
      })
  }

  load()
}
