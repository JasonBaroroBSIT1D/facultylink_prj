window.ReviewerPageInit = function (el) {
  FacultyLinkReviewerApi.listRankSimulations().then(function (rows) {
    var body = rows
      .map(function (r) {
        return (
          '<tr><td><strong>' +
          r.faculty +
          '</strong></td><td>' +
          r.currentRank +
          '</td><td>' +
          r.kra1 +
          '</td><td>' +
          r.kra2 +
          '</td><td>' +
          r.kra3 +
          '</td><td>' +
          r.kra4 +
          '</td><td>' +
          r.totalPoints +
          '</td><td>' +
          r.simulatedRank +
          '</td><td>' +
          r.missing +
          '</td><td>' +
          r.status +
          '</td></tr>'
        )
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Rank Simulation Review</h1>' +
      '<p class="admin-page-desc">Advisory preview only — not an official promotion decision. Point totals and ranks come from the shared backend when integrated.</p>' +
      '<div class="admin-panel"><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Faculty</th><th>Current rank</th><th>KRA I</th><th>KRA II</th><th>KRA III</th><th>KRA IV</th><th>Total eligible pts</th><th>Simulated rank</th><th>Missing</th><th>Status</th></tr></thead><tbody>' +
      body +
      '</tbody></table></div></div>' +
      '<p class="reviewer-note">Official DBM–CHED evaluation remains with authorized bodies. FacultyLink does not confer rank.</p>'
  })
}
