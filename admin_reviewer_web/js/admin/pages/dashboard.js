window.AdminPageInit = function (el) {
  FacultyLinkAdminApi.getDashboardSummary().then(function (data) {
    var cards = data.cards
      .map(function (c) {
        return (
          '<article class="admin-stat-card admin-stat-card--' +
          (c.tone || 'blue') +
          '"><div class="admin-stat-card__label">' +
          c.label +
          '</div><div class="admin-stat-card__value">' +
          c.value +
          '</div><div class="admin-stat-card__trend">' +
          c.trend +
          '</div></article>'
        )
      })
      .join('')

    var activity = data.recentActivity
      .map(function (a) {
        return '<li><time>' + a.time + '</time>' + a.text + '</li>'
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Dashboard Overview</h1>' +
      '<p class="admin-page-desc">Institution-wide summary for faculty evaluation, document flow, and rank simulation monitoring (mock metrics).</p>' +
      '<div class="admin-card-grid">' +
      cards +
      '</div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Recent Activity</h2></div><ul class="admin-activity">' +
      activity +
      '</ul></div>'
  })
}
