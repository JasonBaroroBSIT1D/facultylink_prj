window.AdminPageInit = function (el) {
  function loadKras() {
    if (window.FacultyLinkKraStructure && FacultyLinkKraStructure.buildAdminKras) {
      return FacultyLinkKraStructure.buildAdminKras()
    }
    return []
  }

  function renderCriterion(c) {
    var indicators =
      c.indicators && c.indicators.length
        ? c.indicators
            .map(function (i) {
              return '<li>' + i + '</li>'
            })
            .join('')
        : '<li class="admin-empty-hint">No indicators configured yet.</li>'

    var evidence =
      c.evidence && c.evidence.length
        ? c.evidence
            .map(function (e) {
              return '<li>' + e + '</li>'
            })
            .join('')
        : '<li class="admin-empty-hint">Evidence requirements pending backend config.</li>'

    return (
      '<details class="admin-kra-block" open><summary><strong>Criterion ' +
      c.code +
      '</strong> — ' +
      c.title +
      '</summary><div class="admin-kra-block__body">' +
      '<p><strong>Indicators</strong></p><ul>' +
      indicators +
      '</ul><p><strong>Evidence requirements</strong></p><ul>' +
      evidence +
      '</ul>' +
      (c.capNote ? '<p class="admin-page-desc" style="margin:12px 0 0">' + c.capNote + '</p>' : '') +
      '<button type="button" class="fl-btn fl-btn--ghost" style="margin-top:12px;padding:8px 14px;font-size:0.85rem" disabled>Edit (backend)</button></div></details>'
    )
  }

  function renderKraDetail(kra) {
    if (!kra) {
      return '<p class="admin-page-desc">Select a KRA to view criteria and indicators.</p>'
    }
    return (
      '<div class="admin-kra-detail__head"><h2>' +
      kra.title +
      '</h2>' +
      (kra.weightNote ? '<p class="admin-page-desc">' + kra.weightNote + '</p>' : '') +
      '<p class="admin-sample-tag">Sample configuration data</p></div>' +
      '<div class="admin-kra-detail__criteria">' +
      kra.criteria.map(renderCriterion).join('') +
      '</div>'
    )
  }

  function renderOverviewCards(kras, activeId) {
    return kras
      .map(function (k) {
        var count = k.criteria ? k.criteria.length : 0
        return (
          '<button type="button" class="admin-kra-card' +
          (k.id === activeId ? ' is-active' : '') +
          '" data-kra-select="' +
          k.id +
          '"><span class="admin-kra-card__title">' +
          k.title.split('—')[0].trim() +
          '</span><span class="admin-kra-card__meta">' +
          count +
          ' criteria</span></button>'
        )
      })
      .join('')
  }

  FacultyLinkAdminApi.getKraConfig().then(function (cfg) {
    var kras = (cfg && cfg.kras && cfg.kras.length ? cfg.kras : loadKras()).filter(Boolean)
    if (!kras.length) {
      el.innerHTML =
        '<h1 class="admin-page-title">KRA Configuration</h1>' +
        '<p class="admin-page-desc">Unable to load KRA hierarchy. Ensure kraStructure.js is loaded.</p>'
      return
    }

    var activeId = kras[0].id

    el.innerHTML =
      '<h1 class="admin-page-title">KRA Configuration</h1>' +
      '<p class="admin-page-desc">Explore and manage the four Key Result Areas, their criteria, indicators, and supporting evidence requirements.</p>' +
      '<div class="admin-kra-overview" id="kra-overview">' +
      renderOverviewCards(kras, activeId) +
      '</div>' +
      '<div class="admin-panel admin-kra-detail" id="kra-detail"></div>'

    var detail = document.getElementById('kra-detail')

    function selectKra(id) {
      activeId = id
      document.querySelectorAll('.admin-kra-card').forEach(function (card) {
        card.classList.toggle('is-active', card.getAttribute('data-kra-select') === id)
      })
      var kra = kras.find(function (k) {
        return k.id === id
      })
      detail.innerHTML = renderKraDetail(kra)
    }

    selectKra(activeId)

    document.getElementById('kra-overview').addEventListener('click', function (e) {
      var btn = e.target.closest('[data-kra-select]')
      if (!btn) return
      selectKra(btn.getAttribute('data-kra-select'))
    })
  })
}
