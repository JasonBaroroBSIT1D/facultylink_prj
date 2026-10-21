window.ReviewerPageInit = function (el, h) {
  FacultyLinkReviewerApi.getDashboard().then(function (data) {
    var cards = data.cards
      .map(function (c) {
        return (
          '<article class="admin-stat-card"><div class="admin-stat-card__label">' +
          c.label +
          '</div><div class="admin-stat-card__value">' +
          c.value +
          '</div></article>'
        )
      })
      .join('')
    var activity = data.recentActivity
      .map(function (a) {
        return '<li><time>' + a.time + '</time>' + a.text + '</li>'
      })
      .join('')
    var attn = data.attention
      .map(function (d) {
        return (
          '<tr><td>' +
          d.id +
          '</td><td>' +
          d.faculty +
          '</td><td>' +
          d.title +
          '</td><td>' +
          h.statusBadge(d.status) +
          '</td><td><a href="document-detail.html?id=' +
          encodeURIComponent(d.id) +
          '">Review</a></td></tr>'
        )
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Reviewer Dashboard</h1>' +
      '<p class="admin-page-desc">Overview of assigned faculty, verification queue, and assessment activity (mock).</p>' +
      '<div class="admin-card-grid">' +
      cards +
      '</div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Documents requiring attention</h2></div>' +
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>ID</th><th>Faculty</th><th>Document</th><th>Status</th><th></th></tr></thead><tbody>' +
      attn +
      '</tbody></table></div></div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Recent review activity</h2></div><ul class="admin-activity">' +
      activity +
      '</ul></div>' +
      '<div class="admin-toolbar"><a href="assigned-faculty.html" class="fl-btn fl-btn--primary">Assigned Faculty</a>' +
      '<a href="document-review.html" class="fl-btn fl-btn--ghost">Document Review Queue</a></div>'
  })
}
