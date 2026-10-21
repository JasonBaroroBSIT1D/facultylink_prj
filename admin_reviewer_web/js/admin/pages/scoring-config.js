window.AdminPageInit = function (el, helpers) {
  FacultyLinkAdminApi.getScoringRules().then(function (data) {
    function ruleRows(rules) {
      return rules
        .map(function (r) {
          return (
            '<tr><td>' +
            r.id +
            '</td><td><strong>' +
            r.name +
            '</strong><br /><span style="color:var(--fl-text-muted);font-size:0.8rem">' +
            r.description +
            '</span></td><td>' +
            r.type +
            '</td><td>' +
            (r.active
              ? helpers.statusBadge('Active')
              : '<span class="fl-badge fl-badge--muted">Inactive</span>') +
            '</td><td><button type="button" class="fl-btn fl-btn--ghost" style="padding:6px 12px;font-size:0.8rem" disabled>Edit</button></td></tr>'
          )
        })
        .join('')
    }

    el.innerHTML =
      '<h1 class="admin-page-title">Rule-Based Validation &amp; Scoring</h1>' +
      '<p class="admin-page-desc">Admin-defined rules consumed by the Python rule engine — not calculated independently in the browser.</p>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Document validation rules</h2><button type="button" class="fl-btn fl-btn--primary" style="padding:8px 16px" disabled>Add rule</button></div>' +
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Rule</th><th>Type</th><th>Status</th><th></th></tr></thead><tbody>' +
      ruleRows(data.validationRules) +
      '</tbody></table></div></div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Scoring &amp; workflow rules</h2></div>' +
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Rule</th><th>Type</th><th>Status</th><th></th></tr></thead><tbody>' +
      ruleRows(data.scoringRules) +
      '</tbody></table></div></div>' +
      '<p class="admin-page-desc">Documents passing all mandatory checks remain eligible for <strong>System Approved</strong> without mandatory reviewer action.</p>'
  })
}
