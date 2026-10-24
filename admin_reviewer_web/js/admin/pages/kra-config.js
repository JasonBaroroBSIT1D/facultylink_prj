window.AdminPageInit = function (el) {
  var ui = window.FacultyLinkAdminAccountUi || {
    esc: function (v) {
      return String(v == null ? '' : v)
    },
  }

  var KRA_SHELLS = [
    { id: 'kra-i', code: 'KRA I', name: 'Instruction', title: 'KRA I — Instruction', structuralLetters: ['A', 'B', 'C'] },
    {
      id: 'kra-ii',
      code: 'KRA II',
      name: 'Research and Innovation',
      title: 'KRA II — Research and Innovation',
      structuralLetters: ['A', 'B', 'C'],
    },
    {
      id: 'kra-iii',
      code: 'KRA III',
      name: 'Extension or Community Services',
      title: 'KRA III — Extension or Community Services',
      structuralLetters: ['A', 'B', 'C', 'D'],
    },
    {
      id: 'kra-iv',
      code: 'KRA IV',
      name: 'Professional Development',
      title: 'KRA IV — Professional Development',
      structuralLetters: ['A', 'B', 'C', 'D'],
    },
  ]

  function structureMeta() {
    return window.FacultyLinkKraStructure && window.FacultyLinkKraStructure.meta
      ? window.FacultyLinkKraStructure.meta
      : null
  }

  function enrichShell(shell) {
    var meta = structureMeta()
    if (!meta) return shell
    var match = meta.find(function (m) {
      return normalizeCode(m.key) === normalizeCode(shell.code)
    })
    if (!match) return shell
    return Object.assign({}, shell, {
      title: match.title,
      name: match.title.indexOf('—') >= 0 ? match.title.split('—').slice(1).join('—').trim() : shell.name,
      structuralLetters: match.letters ? match.letters.slice() : shell.structuralLetters,
    })
  }

  function normalizeCode(code) {
    return String(code || '')
      .trim()
      .toUpperCase()
      .replace(/\s+/g, ' ')
  }

  function mergeKrasFromApi(apiKras) {
    var byCode = {}
    ;(apiKras || []).forEach(function (k) {
      byCode[normalizeCode(k.code)] = k
    })
    return KRA_SHELLS.map(function (shell) {
      shell = enrichShell(shell)
      var match = byCode[normalizeCode(shell.code)]
      if (!match) {
        return Object.assign({}, shell, { criteria: [], criteria_count: 0, configured: false })
      }
      return Object.assign({}, shell, match, {
        id: match.id != null ? match.id : shell.id,
        title: match.title || match.name || shell.title,
        name: match.name || shell.name,
        configured: !!(match.criteria && match.criteria.length),
      })
    })
  }

  function hasDatabaseRecords(apiKras) {
    return (
      Array.isArray(apiKras) &&
      apiKras.some(function (k) {
        return (k.criteria && k.criteria.length) || (k.criteria_count != null && k.criteria_count > 0)
      })
    )
  }

  function kraIconSvg() {
    return (
      '<svg class="kra-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">' +
      '<rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" stroke-width="1.6"/>' +
      '<path d="M7 9h10M7 13h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
    )
  }

  function sectionIcon(type) {
    var paths = {
      criteria:
        '<path d="M4 6h16M4 12h16M4 18h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
      indicators:
        '<path d="M8 6h8M6 12h12M9 18h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
      evidence:
        '<path d="M8 4h8l2 4v12H6V4z" stroke="currentColor" stroke-width="1.6"/><path d="M8 4v4h8" stroke="currentColor" stroke-width="1.6"/>',
      scoring:
        '<path d="M4 19V5M4 19h16M8 15V9M12 15V7M16 15v-4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
    }
    return (
      '<svg class="kra-section-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">' +
      (paths[type] || paths.criteria) +
      '</svg>'
    )
  }

  function emptySlot(label) {
    return (
      '<div class="kra-empty-slot" role="status">' +
      '<span class="kra-empty-slot__label">' +
      ui.esc(label) +
      '</span>' +
      '<p>Not configured yet</p></div>'
    )
  }

  function loadingHtml() {
    return (
      '<h1 class="admin-page-title">KRA Configuration</h1>' +
      '<div class="admin-loading-state" role="status"><span class="admin-loading-state__spinner"></span><p>Loading KRA configuration…</p></div>'
    )
  }

  function errorHtml(message) {
    return (
      '<h1 class="admin-page-title">KRA Configuration</h1>' +
      '<p class="admin-page-desc">Review and manage Key Result Areas, criteria, indicators, and scoring rules.</p>' +
      '<div class="admin-error-state" role="alert"><p>' +
      ui.esc(message) +
      '</p><button type="button" class="fl-btn fl-btn--primary" id="kra-reload">Try again</button></div>'
    )
  }

  function scoringRulesFromEditing(editing) {
    return (editing && (editing.scoring_rules || editing.scoring_rules_locked)) || []
  }

  function renderConfigurationProfile(editing, uiState) {
    if (!editing) return ''
    var profile = editing.configuration_profile || {}
    var locked = editing.locked_official || {}
    var label =
      profile.configuration_label_display ||
      (profile.configuration_label === 'custom_configuration' ? 'Custom Configuration' : 'Official DBM–CHED Scoring')
    var badgeClass =
      profile.configuration_label === 'custom_configuration' ? 'kra-config-badge kra-config-badge--custom' : 'kra-config-badge'
    var issues =
      editing.locked_scoring_issues && editing.locked_scoring_issues.length
        ? '<p class="admin-form-error">' + ui.esc(editing.locked_scoring_issues.join(' ')) + '</p>'
        : ''
    var rules = scoringRulesFromEditing(editing)
    var critMax =
      profile.criterion_max_points != null ? profile.criterion_max_points : locked.criterion_max_points
    var restoreBtn = uiState.editing
      ? ''
      : '<button type="button" class="fl-btn fl-btn--ghost kra-restore-official" data-kra-restore-official>Restore official defaults</button>'
    var rulesHtml =
      rules.length > 0
        ? '<ul class="kra-rule-list">' +
          rules
            .map(function (rule) {
              return (
                '<li><strong>' +
                ui.esc(rule.indicator_code) +
                '</strong> — ' +
                ui.esc(rule.rule_name) +
                '<br /><span class="kra-muted">Max ' +
                ui.esc(rule.max_points) +
                ' pts · Formula ' +
                ui.esc(rule.formula || '(rating / 100) * max_points') +
                '</span></li>'
              )
            })
            .join('') +
          '</ul>'
        : emptySlot('Scoring rules')
    return (
      '<section class="kra-operational-panel">' +
      '<div class="kra-config-profile-head">' +
      '<h3 class="kra-subhead">Scoring configuration</h3>' +
      '<span class="' +
      badgeClass +
      '">' +
      ui.esc(label) +
      '</span></div>' +
      '<ul class="kra-operational-locked">' +
      '<li>Criterion A maximum: ' +
      ui.esc(critMax) +
      ' points</li>' +
      '<li>Official reference (2026): SET ' +
      ui.esc(locked.set_max_points) +
      ' · SEF ' +
      ui.esc(locked.sef_max_points) +
      ' · Criterion ' +
      ui.esc(locked.criterion_max_points) +
      '</li></ul>' +
      issues +
      rulesHtml +
      restoreBtn +
      '</section>'
    )
  }

  function renderScoringRules(rules) {
    if (!rules || !rules.length) {
      return emptySlot('Scoring rules')
    }
    return (
      '<ul class="kra-rule-list">' +
      rules
        .map(function (rule) {
          var extras = []
          if (rule.max_points != null) extras.push('Max points: ' + rule.max_points)
          if (rule.guideline_version) extras.push('Guideline: ' + rule.guideline_version)
          if (rule.locked) extras.push('Locked')
          return (
            '<li><strong>' +
            ui.esc(rule.rule_name) +
            '</strong> <span class="kra-muted">(' +
            ui.esc(rule.rule_type) +
            ')</span>' +
            (extras.length ? '<br /><span class="kra-muted">' + ui.esc(extras.join(' · ')) + '</span>' : '') +
            '</li>'
          )
        })
        .join('') +
      '</ul>'
    )
  }

  function renderKraEditField(label, controlHtml) {
    return (
      '<div class="admin-form-field admin-form-field--wide">' +
      '<span class="kra-field-label">' +
      ui.esc(label) +
      '</span>' +
      controlHtml +
      '</div>'
    )
  }

  function renderCriterionA(c, editing, uiState) {
    var draft = uiState.draft || {}
    var indDraft = draft.indicators || {}
    var scoringDraft = draft.scoring_rules || {}
    var indicators = (editing && editing.indicators) || c.indicators || []
    var scoringRules = scoringRulesFromEditing(editing)

    var indicatorHtml = indicators
      .map(function (ind) {
        var d = indDraft[ind.indicator_id] || ind
        var nameVal = d.name != null ? d.name : ind.name
        var evVal = d.required_evidence != null ? d.required_evidence : ind.required_evidence || ''
        var rule = scoringRules.find(function (r) {
          return r.indicator_code === ind.code
        })
        var ruleDraft = (rule && scoringDraft[rule.rule_id]) || rule || {}
        if (uiState.editing) {
          return (
            '<section class="kra-indicator kra-indicator--edit-block" data-indicator-id="' +
            ind.indicator_id +
            '">' +
            '<h4 class="kra-indicator__edit-title">' +
            ui.esc(ind.code) +
            (ind.name ? ' — ' + ui.esc(nameVal) : '') +
            '</h4>' +
            renderKraEditField(
              'Display name',
              '<input type="text" class="admin-field-input" name="ind_name_' +
                ind.indicator_id +
                '" value="' +
                ui.esc(nameVal) +
                '" maxlength="200" required autocomplete="off" />'
            ) +
            renderKraEditField(
              'Evidence requirements',
              '<textarea class="admin-field-input kra-field-textarea" name="ind_evidence_' +
                ind.indicator_id +
                '" rows="4" maxlength="8000" wrap="soft">' +
                ui.esc(evVal) +
                '</textarea>'
            ) +
            (rule
              ? '<div class="kra-scoring-edit" data-rule-id="' +
                rule.rule_id +
                '">' +
                '<p class="kra-subhead">Scoring (SET/SEF)</p>' +
                renderKraEditField(
                  'Maximum points',
                  '<input type="number" class="admin-field-input" name="rule_max_' +
                    rule.rule_id +
                    '" min="0.01" max="100" step="0.01" value="' +
                    ui.esc(ruleDraft.max_points != null ? ruleDraft.max_points : '') +
                    '" required />'
                ) +
                renderKraEditField(
                  'Formula (rating and max_points only)',
                  '<input type="text" class="admin-field-input" name="rule_formula_' +
                    rule.rule_id +
                    '" value="' +
                    ui.esc(ruleDraft.formula || '(rating / 100) * max_points') +
                    '" maxlength="200" required autocomplete="off" />'
                ) +
                '</div>'
              : '') +
            '</section>'
          )
        }
        return (
          '<div class="kra-indicator">' +
          '<p class="kra-indicator__head"><strong>' +
          ui.esc(ind.code) +
          '</strong> — ' +
          ui.esc(ind.name) +
          '</p>' +
          '<p class="kra-subhead">Evidence requirements</p>' +
          (ind.required_evidence
            ? '<p class="kra-muted">' + ui.esc(ind.required_evidence) + '</p>'
            : emptySlot('Evidence requirements')) +
          '<p class="kra-subhead">Scoring rules</p>' +
          renderScoringRules(
            (c.indicators || []).find(function (row) {
              return row.indicator_id === ind.indicator_id
            })
              ? (c.indicators || []).find(function (row) {
                  return row.indicator_id === ind.indicator_id
                }).scoring_rules
              : []
          ) +
          '</div>'
        )
      })
      .join('')

    var notice = uiState.message
      ? '<p class="' +
        (uiState.message.type === 'error' ? 'admin-form-error' : 'ep-notice') +
        '" role="status">' +
        ui.esc(uiState.message.text) +
        '</p>'
      : ''

    var editStartActions = uiState.editing
      ? ''
      : '<div class="kra-criterion-a-edit-actions kra-criterion-a-edit-actions--top">' +
        '<button type="button" class="fl-btn fl-btn--primary" data-kra-a-edit>Edit configuration</button></div>'

    var editFooterActions = uiState.editing
      ? '<div class="kra-criterion-a-edit-actions">' +
        '<button type="button" class="fl-btn fl-btn--primary" data-kra-a-save>Save changes</button>' +
        '<button type="button" class="fl-btn fl-btn--ghost" data-kra-a-cancel>Cancel</button></div>'
      : ''

    var nameVal = uiState.editing ? draft.criterion_name || c.name : c.name
    var descVal = uiState.editing ? draft.description || c.description || '' : c.description || ''

    var editFormHtml = uiState.editing
      ? '<div class="kra-criterion-a-edit-form">' +
        '<section class="kra-edit-section">' +
        '<h4 class="kra-edit-section__title">Criterion details</h4>' +
        renderKraEditField(
          'Criterion name',
          '<input type="text" class="admin-field-input" name="criterion_name" value="' +
            ui.esc(nameVal) +
            '" maxlength="200" required autocomplete="off" />'
        ) +
        renderKraEditField(
          'Description',
          '<textarea class="admin-field-input kra-field-textarea" name="criterion_description" rows="4" maxlength="8000" wrap="soft">' +
            ui.esc(descVal) +
            '</textarea>'
        ) +
        renderKraEditField(
          'Criterion A maximum points',
          '<input type="number" class="admin-field-input" name="criterion_max_points" min="1" max="100" step="1" value="' +
            ui.esc(
              draft.criterion_max_points != null
                ? draft.criterion_max_points
                : (editing.configuration_profile && editing.configuration_profile.criterion_max_points) || 60
            ) +
            '" required />'
        ) +
        '</section>' +
        '<section class="kra-edit-section">' +
        '<h4 class="kra-edit-section__title">Indicators (SET / SEF)</h4>' +
        indicatorHtml +
        '</section>' +
        editFooterActions +
        '</div>'
      : ''

    return (
      '<details class="admin-kra-block kra-criterion" open data-kra-criterion-a>' +
      '<summary><span><strong>Criterion ' +
      ui.esc(c.code) +
      '</strong> — ' +
      ui.esc(c.name) +
      '</span><span class="kra-criterion__meta">SET/SEF · full configuration</span></summary>' +
      '<div class="admin-kra-block__body">' +
      renderConfigurationProfile(editing, uiState) +
      notice +
      editStartActions +
      (uiState.editing
        ? editFormHtml
        : (c.description ? '<p class="kra-muted">' + ui.esc(c.description) + '</p>' : '') +
          '<p class="kra-subhead">Indicators</p>' +
          indicatorHtml) +
      '</div></details>'
    )
  }

  function renderCriterion(c, editing, uiState, kraCode) {
    if (normalizeCode(kraCode) === normalizeCode('KRA I') && String(c.code).toUpperCase() === 'A' && editing) {
      return renderCriterionA(c, editing, uiState)
    }
    var indicators =
      c.indicators && c.indicators.length
        ? c.indicators
            .map(function (ind) {
              return (
                '<div class="kra-indicator">' +
                '<p class="kra-indicator__head"><strong>' +
                ui.esc(ind.code) +
                '</strong> — ' +
                ui.esc(ind.name) +
                '</p>' +
                '<p class="kra-subhead">Evidence requirements</p>' +
                (ind.required_evidence
                  ? '<p class="kra-muted">' + ui.esc(ind.required_evidence) + '</p>'
                  : emptySlot('Evidence requirements')) +
                '<p class="kra-subhead">Scoring rules</p>' +
                renderScoringRules(ind.scoring_rules) +
                '</div>'
              )
            })
            .join('')
        : emptySlot('Indicators')

    return (
      '<details class="admin-kra-block kra-criterion" open>' +
      '<summary><span><strong>Criterion ' +
      ui.esc(c.code) +
      '</strong> — ' +
      ui.esc(c.name) +
      '</span><span class="kra-criterion__meta">' +
      (c.indicator_count != null ? c.indicator_count : c.indicators ? c.indicators.length : 0) +
      ' indicators</span></summary>' +
      '<div class="admin-kra-block__body">' +
      (c.description ? '<p class="kra-muted">' + ui.esc(c.description) + '</p>' : '') +
      '<p class="kra-subhead">Indicators</p>' +
      indicators +
      '</div></details>'
    )
  }

  function renderStructuralCriterion(letter) {
    return (
      '<details class="admin-kra-block kra-criterion">' +
      '<summary><span><strong>Criterion ' +
      ui.esc(letter) +
      '</strong> — <span class="kra-muted">Pending official configuration</span></span></summary>' +
      '<div class="admin-kra-block__body">' +
      '<p class="kra-subhead">Indicators</p>' +
      emptySlot('Indicators') +
      '<p class="kra-subhead">Evidence requirements</p>' +
      emptySlot('Evidence requirements') +
      '<p class="kra-subhead">Scoring rules</p>' +
      emptySlot('Scoring rules') +
      '</div></details>'
    )
  }

  function renderEmptyWorkspace(kra) {
    var displayTitle = kra.title || kra.code
    var letters = kra.structuralLetters || []
    var criteriaPanels = letters.length
      ? letters.map(renderStructuralCriterion).join('')
      : emptySlot('Criteria')
    return (
      '<div class="kra-workspace">' +
      '<header class="kra-workspace__head">' +
      '<div class="kra-workspace__title-row">' +
      kraIconSvg() +
      '<div><h2>' +
      ui.esc(displayTitle) +
      '</h2>' +
      '<p class="kra-workspace__intro">Structural criterion slots (letters A–D) match the FacultyLink project convention. Names, indicators, evidence, and scoring will appear here once verified PostgreSQL records are imported.</p>' +
      '</div></div>' +
      '<span class="kra-status-badge kra-status-badge--empty">Awaiting PostgreSQL configuration</span>' +
      '<p class="kra-readonly-note">Read-only view. No sample or mock scoring data is shown. See docs/KRA_CONFIGURATION_SOURCES_AND_IMPORT_PLAN.md for import steps.</p>' +
      '</header>' +
      '<div class="kra-workspace__criteria">' +
      '<h3 class="kra-workspace__section-title">Criteria structure (' +
      letters.length +
      ' slots)</h3>' +
      criteriaPanels +
      '</div></div>'
    )
  }

  function renderConfiguredWorkspace(kra, editing, uiState) {
    return (
      '<div class="kra-workspace">' +
      '<header class="kra-workspace__head">' +
      '<div class="kra-workspace__title-row">' +
      kraIconSvg() +
      '<div><h2>' +
      ui.esc(kra.title || kra.name) +
      '</h2>' +
      (kra.description ? '<p class="admin-page-desc">' + ui.esc(kra.description) + '</p>' : '') +
      (kra.guideline_version
        ? '<p class="kra-guideline-tag">Guideline version: ' + ui.esc(kra.guideline_version) + '</p>'
        : '') +
      '</div></div>' +
      '<span class="kra-status-badge kra-status-badge--active">Configured in PostgreSQL</span>' +
      (normalizeCode(kra.code) !== normalizeCode('KRA I')
        ? '<p class="kra-readonly-note">Read-only. KRA I Criterion A (SET/SEF) is the only editable configuration in this release.</p>'
        : '') +
      '</header>' +
      '<div class="kra-workspace__criteria">' +
      '<h3 class="kra-workspace__section-title">Criteria &amp; indicators</h3>' +
      kra.criteria
        .map(function (c) {
          return renderCriterion(c, editing, uiState, kra.code)
        })
        .join('') +
      '</div></div>'
    )
  }

  function renderKraDetail(kra, editing, uiState) {
    if (!kra) {
      return '<p class="admin-page-desc">Select a KRA to review its configuration workspace.</p>'
    }
    if (kra.criteria && kra.criteria.length) {
      return renderConfiguredWorkspace(kra, editing, uiState)
    }
    return renderEmptyWorkspace(kra)
  }

  function renderOverviewCards(kras, activeId) {
    return kras
      .map(function (k) {
        var count = k.criteria_count != null ? k.criteria_count : k.criteria ? k.criteria.length : 0
        var slotCount = k.structuralLetters ? k.structuralLetters.length : count
        var status =
          count > 0
            ? count + ' criteria in database'
            : slotCount + ' structural slots · not in database yet'
        return (
          '<button type="button" class="admin-kra-card' +
          (String(k.id) === String(activeId) ? ' is-active' : '') +
          '" data-kra-select="' +
          ui.esc(k.id) +
          '">' +
          '<span class="admin-kra-card__icon">' +
          kraIconSvg() +
          '</span>' +
          '<span class="admin-kra-card__title">' +
          ui.esc(k.code || k.title) +
          '</span>' +
          '<span class="admin-kra-card__meta">' +
          ui.esc(status) +
          '</span></button>'
        )
      })
      .join('')
  }

  function buildDraftFromEditing(editing) {
    if (!editing) return {}
    var ind = {}
    ;(editing.indicators || []).forEach(function (row) {
      ind[row.indicator_id] = { name: row.name, required_evidence: row.required_evidence || '' }
    })
    var scoring = {}
    scoringRulesFromEditing(editing).forEach(function (rule) {
      scoring[rule.rule_id] = {
        max_points: rule.max_points,
        formula: rule.formula || '(rating / 100) * max_points',
      }
    })
    var profile = editing.configuration_profile || {}
    return {
      criterion_name: editing.criterion_name,
      description: editing.description || '',
      criterion_max_points: profile.criterion_max_points != null ? profile.criterion_max_points : 60,
      indicators: ind,
      scoring_rules: scoring,
    }
  }

  function mount(cfg) {
    var kras = mergeKrasFromApi((cfg && cfg.kras) || [])
    var dbHasRecords = hasDatabaseRecords(cfg && cfg.kras)
    var activeId = kras[0].id
    var editingBundle = cfg && cfg.kra_i_criterion_a_editing
    var uiState = {
      editing: false,
      draft: buildDraftFromEditing(editingBundle),
      message: null,
    }

    el.innerHTML =
      '<h1 class="admin-page-title">KRA Configuration</h1>' +
      '<p class="admin-page-desc">Review and manage Key Result Areas, criteria, indicators, and scoring rules.</p>' +
      (dbHasRecords && cfg.guideline_version
        ? '<p class="kra-guideline-tag">Active guideline version: ' + ui.esc(cfg.guideline_version) + '</p>'
        : '') +
      (!dbHasRecords
        ? '<div class="kra-db-notice" role="status">' +
          '<strong>No KRA rows in PostgreSQL yet.</strong> You can browse the four KRAs and criterion letter slots below. Verified criteria, indicators, and scoring will replace placeholders after an approved import (see docs/KRA_CONFIGURATION_SOURCES_AND_IMPORT_PLAN.md).' +
          '</div>'
        : '') +
      '<div class="admin-kra-overview" id="kra-overview">' +
      renderOverviewCards(kras, activeId) +
      '</div>' +
      '<div class="admin-panel admin-kra-detail" id="kra-detail"></div>'

    var detail = document.getElementById('kra-detail')

    function syncKraTreeFromEditing(editing) {
      if (!editing) return
      var kraI = kras.find(function (k) {
        return normalizeCode(k.code) === normalizeCode('KRA I')
      })
      if (!kraI || !kraI.criteria) return
      var critA = kraI.criteria.find(function (c) {
        return String(c.code).toUpperCase() === 'A'
      })
      if (!critA) return
      critA.name = editing.criterion_name
      critA.description = editing.description
      ;(editing.indicators || []).forEach(function (ind) {
        var row = (critA.indicators || []).find(function (r) {
          return r.indicator_id === ind.indicator_id
        })
        if (row) {
          row.name = ind.name
          row.required_evidence = ind.required_evidence
        }
      })
    }

    function bindCriterionAEvents() {
      var block = detail.querySelector('[data-kra-criterion-a]')
      if (!block) return
      var editBtn = block.querySelector('[data-kra-a-edit]')
      if (editBtn) {
        editBtn.addEventListener('click', function () {
          uiState.editing = true
          uiState.message = null
          uiState.draft = buildDraftFromEditing(editingBundle)
          paintDetail()
        })
      }
      var cancelBtn = block.querySelector('[data-kra-a-cancel]')
      if (cancelBtn) {
        cancelBtn.addEventListener('click', function () {
          uiState.editing = false
          uiState.message = null
          paintDetail()
        })
      }
      var restoreBtn = block.querySelector('[data-kra-restore-official]')
      if (restoreBtn) {
        restoreBtn.addEventListener('click', function () {
          if (!window.confirm('Restore official DBM–CHED 2026 defaults (60 / 36 / 24 and standard formulas)?')) {
            return
          }
          restoreBtn.disabled = true
          FacultyLinkAdminHttp.ensureCsrf()
            .then(function () {
              return FacultyLinkAdminApi.updateKraICriterionAMetadata({ restore_official_defaults: true })
            })
            .then(function (body) {
              editingBundle = body.kra_i_criterion_a_editing || editingBundle
              syncKraTreeFromEditing(editingBundle)
              uiState.draft = buildDraftFromEditing(editingBundle)
              uiState.message = { type: 'success', text: 'Official defaults restored.' }
              paintDetail()
            })
            .catch(function (err) {
              uiState.message = { type: 'error', text: err.message || 'Unable to restore defaults.' }
              paintDetail()
            })
            .finally(function () {
              restoreBtn.disabled = false
            })
        })
      }
      var saveBtn = block.querySelector('[data-kra-a-save]')
      if (saveBtn) {
        saveBtn.addEventListener('click', function () {
          uiState.message = null
          var nameInput = block.querySelector('[name="criterion_name"]')
          var descInput = block.querySelector('[name="criterion_description"]')
          if (!nameInput) return
          var payload = {
            criterion_name: nameInput.value.trim(),
            description: descInput ? descInput.value.trim() : '',
            indicators: [],
          }
          block.querySelectorAll('[data-indicator-id]').forEach(function (node) {
            var id = Number(node.getAttribute('data-indicator-id'))
            var n = node.querySelector('[name="ind_name_' + id + '"]')
            var e = node.querySelector('[name="ind_evidence_' + id + '"]')
            payload.indicators.push({
              indicator_id: id,
              indicator_name: n ? n.value.trim() : '',
              required_evidence: e ? e.value.trim() : '',
            })
          })
          var critMaxInput = block.querySelector('[name="criterion_max_points"]')
          if (critMaxInput) {
            payload.criterion_max_points = Number(critMaxInput.value)
          }
          payload.scoring_rules = []
          block.querySelectorAll('[data-rule-id]').forEach(function (node) {
            var ruleId = Number(node.getAttribute('data-rule-id'))
            var maxInput = node.querySelector('[name="rule_max_' + ruleId + '"]')
            var formulaInput = node.querySelector('[name="rule_formula_' + ruleId + '"]')
            if (!maxInput || !formulaInput) return
            payload.scoring_rules.push({
              rule_id: ruleId,
              max_points: Number(maxInput.value),
              formula: formulaInput.value.trim(),
            })
          })
          if (
            !window.confirm(
              'Save KRA I Criterion A configuration (metadata, evidence, and scoring)? Subsequent uploads will use these settings.'
            )
          ) {
            return
          }
          saveBtn.disabled = true
          FacultyLinkAdminHttp.ensureCsrf()
            .then(function () {
              return FacultyLinkAdminApi.updateKraICriterionAMetadata(payload)
            })
            .then(function (body) {
              editingBundle = body.kra_i_criterion_a_editing || editingBundle
              syncKraTreeFromEditing(editingBundle)
              uiState.editing = false
              uiState.draft = buildDraftFromEditing(editingBundle)
              uiState.message = { type: 'success', text: 'Configuration saved.' }
              paintDetail()
            })
            .catch(function (err) {
              uiState.message = { type: 'error', text: err.message || 'Unable to save.' }
              paintDetail()
            })
            .finally(function () {
              saveBtn.disabled = false
            })
        })
      }
    }

    function paintDetail() {
      var kra = kras.find(function (k) {
        return String(k.id) === String(activeId)
      })
      detail.innerHTML = renderKraDetail(kra, editingBundle, uiState)
      bindCriterionAEvents()
    }

    function selectKra(id) {
      activeId = id
      uiState.editing = false
      uiState.message = null
      document.querySelectorAll('.admin-kra-card').forEach(function (card) {
        card.classList.toggle('is-active', card.getAttribute('data-kra-select') === String(id))
      })
      paintDetail()
    }

    selectKra(activeId)
    document.getElementById('kra-overview').addEventListener('click', function (e) {
      var btn = e.target.closest('[data-kra-select]')
      if (!btn) return
      selectKra(btn.getAttribute('data-kra-select'))
    })
  }

  function load() {
    el.innerHTML = loadingHtml()
    FacultyLinkAdminHttp.ensureCsrf()
      .then(function () {
        return FacultyLinkAdminApi.getKraConfig()
      })
      .then(mount)
      .catch(function (err) {
        el.innerHTML = errorHtml(err.message || 'Unable to load KRA configuration.')
        var btn = document.getElementById('kra-reload')
        if (btn) btn.addEventListener('click', load)
      })
  }

  load()
}
