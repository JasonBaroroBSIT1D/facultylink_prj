window.AdminPageInit = function (el) {
  FacultyLinkAdminApi.listRankSimulationMonitoring().then(function (rows) {
    var body = rows
      .map(function (r) {
        return (
          '<tr><td><strong>' +
          r.faculty +
          '</strong></td><td>' +
          r.currentRank +
          '</td><td>' +
          r.simulated +
          '</td><td>' +
          r.eligiblePts +
          '</td><td>' +
          r.missing +
          '</td><td>' +
          r.updated +
          '</td></tr>'
        )
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Rank Simulation Monitoring</h1>' +
      '<p class="admin-page-desc">Preview faculty rank readiness from simulated totals — official DBM–CHED evaluation is separate. Point totals shown as “—” until backend integration.</p>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Simulations</h2></div>' +
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Faculty</th><th>Current rank</th><th>Simulated rank</th><th>Eligible pts</th><th>Missing (mock)</th><th>Updated</th></tr></thead><tbody>' +
      body +
      '</tbody></table></div></div>'
  })
}
