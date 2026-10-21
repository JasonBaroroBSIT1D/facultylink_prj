window.AdminPageInit = function (el) {
  FacultyLinkAdminApi.getKraConfig().then(function (cfg) {
    var tabs = cfg.kras
      .map(function (k, i) {
        return (
          '<button type="button" class="admin-tab' +
          (i === 0 ? ' is-active' : '') +
          '" data-kra-tab="' +
          k.id +
          '">' +
          k.title.split('—')[0].trim() +
          '</button>'
        )
      })
      .join('')

    function renderKra(kra) {
      var criteria = kra.criteria
        .map(function (c) {
          return (
            '<div class="admin-kra-block"><h3>Criterion ' +
            c.code +
            ' — ' +
            c.title +
            '</h3>' +
            '<p><strong>Indicators:</strong></p><ul>' +
            c.indicators.map(function (i) {
              return '<li>' + i + '</li>'
            }).join('') +
            '</ul><p><strong>Evidence requirements:</strong></p><ul>' +
            c.evidence.map(function (e) {
              return '<li>' + e + '</li>'
            }).join('') +
            '</ul><p class="admin-page-desc" style="margin:12px 0 0">' +
            c.capNote +
            '</p>' +
            '<button type="button" class="fl-btn fl-btn--ghost" style="margin-top:12px;padding:8px 14px;font-size:0.85rem" disabled>Edit (backend)</button></div>'
          )
        })
        .join('')

      return (
        '<h2 style="margin:0;padding:16px 20px;border-bottom:1px solid var(--fl-border)">' +
        kra.title +
        '</h2>' +
        '<p style="padding:12px 20px 0;margin:0;color:var(--fl-text-muted);font-size:0.85rem">' +
        (kra.weightNote || '') +
        '</p>' +
        criteria
      )
    }

    el.innerHTML =
      '<h1 class="admin-page-title">KRA Configuration</h1>' +
      '<p class="admin-page-desc">Configure four KRAs with criteria, indicators, evidence requirements, and scoring caps — values supplied by the shared backend when connected.</p>' +
      '<div class="admin-tabs" id="kra-tabs">' +
      tabs +
      '</div>' +
      '<div class="admin-panel" id="kra-panel"></div>'

    var panel = document.getElementById('kra-panel')
    panel.innerHTML = renderKra(cfg.kras[0])

    document.getElementById('kra-tabs').addEventListener('click', function (e) {
      var btn = e.target.closest('[data-kra-tab]')
      if (!btn) return
      document.querySelectorAll('.admin-tab').forEach(function (t) {
        t.classList.remove('is-active')
      })
      btn.classList.add('is-active')
      var kra = cfg.kras.find(function (k) {
        return k.id === btn.getAttribute('data-kra-tab')
      })
      if (kra) panel.innerHTML = renderKra(kra)
    })
  })
}
