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
          if (rule.cap != null) extras.push('Cap: ' + rule.cap)
          if (rule.contribution != null) extras.push('Contribution: ' + rule.contribution)
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

  function renderCriterion(c) {
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

  function renderConfiguredWorkspace(kra) {
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
      '<p class="kra-readonly-note">Read-only view. Editing will be available when authorized backend endpoints are implemented.</p>' +
      '</header>' +
      '<div class="kra-workspace__criteria">' +
      '<h3 class="kra-workspace__section-title">Criteria &amp; indicators</h3>' +
      kra.criteria.map(renderCriterion).join('') +
      '</div></div>'
    )
  }

  function renderKraDetail(kra) {
    if (!kra) {
      return '<p class="admin-page-desc">Select a KRA to review its configuration workspace.</p>'
    }
    if (kra.criteria && kra.criteria.length) {
      return renderConfiguredWorkspace(kra)
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

  function mount(cfg) {
    var kras = mergeKrasFromApi((cfg && cfg.kras) || [])
    var dbHasRecords = hasDatabaseRecords(cfg && cfg.kras)
    var activeId = kras[0].id

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

    function selectKra(id) {
      activeId = id
      document.querySelectorAll('.admin-kra-card').forEach(function (card) {
        card.classList.toggle('is-active', card.getAttribute('data-kra-select') === String(id))
      })
      var kra = kras.find(function (k) {
        return String(k.id) === String(id)
      })
      detail.innerHTML = renderKraDetail(kra)
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
