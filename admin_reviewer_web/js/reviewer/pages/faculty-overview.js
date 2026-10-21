window.ReviewerPageInit = function (el) {
  var id = FacultyLinkReviewerUtils.queryParam('id') || 'F-001'
  FacultyLinkReviewerApi.getFacultyOverview(id).then(function (overview) {
    if (!overview) {
      el.innerHTML = '<p class="admin-empty">Faculty not found (mock).</p>'
      return
    }
    var kra = overview.kraSummary
      .map(function (k) {
        return (
          '<div class="admin-kra-block"><h3>' +
          k.kra +
          '</h3><p>' +
          k.progress +
          '</p><p style="font-size:0.85rem;color:var(--fl-text-muted)">' +
          k.docs +
          ' documents (mock)</p></div>'
        )
      })
      .join('')

    el.innerHTML =
      '<a href="assigned-faculty.html" class="fl-btn fl-btn--ghost" style="margin-bottom:16px;padding:8px 14px">← Back to Assigned Faculty</a>' +
      '<h1 class="admin-page-title">' +
      overview.name +
      '</h1>' +
      '<p class="admin-page-desc">Assessment overview by KRA I–IV (KRA → Criterion → Indicator hierarchy in KRA Assessment).</p>' +
      '<div class="admin-panel">' +
      kra +
      '</div>' +
      '<a href="kra-assessment.html?faculty=' +
      encodeURIComponent(id) +
      '" class="fl-btn fl-btn--primary">Open KRA Assessment</a>'
  })
}
