window.ReviewerPageInit = function (el) {
  var store = FacultyLinkEvaluationPeriods
  var ui = FacultyLinkPeriodUI

  function registerBlock(rows) {
    if (!rows.length) return ''
    return (
      '<section class="admin-panel" style="margin-top:20px"><div class="admin-panel__head"><h2>All evaluation periods</h2></div><div class="admin-panel__body">' +
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Academic year</th><th>Semester</th><th>Status</th><th>Reviews</th></tr></thead><tbody>' +
      rows
        .map(function (p) {
          return (
            '<tr><td>' +
            ui.esc(p.academicYear) +
            '</td><td>' +
            ui.esc(p.semester) +
            '</td><td>' +
            ui.badge(p) +
            '</td><td>' +
            (p.reviewEnabled ? 'Enabled' : 'Paused') +
            '</td></tr>'
          )
        })
        .join('') +
      '</tbody></table></div></div></section>'
    )
  }

  function paint() {
    var rows = store.list()
    var period = store.focus(rows)
    el.innerHTML =
      '<div class="ep-page ep-page--config">' +
      '<h1 class="admin-page-title">Evaluation Schedule</h1>' +
      '<p class="admin-page-desc">Faculty evaluation period dates configured by your administrator.</p>' +
      '<section class="admin-panel ep-config-card">' +
      '<div class="admin-panel__head"><h2>Evaluation Period</h2><span class="ep-zone">Asia/Manila · UTC+8</span></div>' +
      '<div class="admin-panel__body ep-config-card__body">' +
      (period
        ? '<dl class="ep-config-dl">' +
          '<div><dt>Evaluation cycle / academic year</dt><dd>' +
          ui.esc(period.academicYear || period.name) +
          '</dd></div>' +
          '<div><dt>Opening</dt><dd>' +
          ui.format(period.opensAt) +
          '</dd></div>' +
          '<div><dt>Closing</dt><dd>' +
          ui.format(period.closesAt) +
          '</dd></div>' +
          '<div><dt>Evaluation status</dt><dd>' +
          ui.badge(period) +
          '</dd></div>' +
          '<div><dt>Faculty submissions</dt><dd>' +
          (period.submissionEnabled ? 'Enabled' : 'Paused') +
          '</dd></div>' +
          '<div><dt>Reviewer activities</dt><dd>' +
          (period.reviewEnabled ? 'Enabled' : 'Paused') +
          '</dd></div>' +
          '</dl>' +
          '<p class="ep-config-note">' +
          ui.esc(ui.accessMessage(period, 'reviewer')) +
          '</p>'
        : '<p class="ep-empty">No evaluation period is configured yet. Contact your administrator.</p>') +
      '</div></section>' +
      registerBlock(rows) +
      '<p class="ep-footnote">Read-only view · Schedules are loaded from PostgreSQL.</p></div>'
  }

  el.innerHTML = '<p class="ep-empty" role="status">Loading evaluation schedule…</p>'
  FacultyLinkReviewerHttp.ensureCsrf()
    .then(function () {
      return FacultyLinkReviewerApi.listEvaluationPeriods()
    })
    .then(function () {
      store.subscribe(paint)
      paint()
    })
    .catch(function () {
      el.innerHTML =
        '<p class="ep-empty" role="alert">Unable to load the evaluation schedule. Reload this page to try again.</p>'
    })
}
