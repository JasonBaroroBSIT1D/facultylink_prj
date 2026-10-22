window.ReviewerPageInit = async function (el) {
  var facultyId = FacultyLinkReviewerUtils.queryParam('faculty') || 'F-001'
  var periodId = FacultyLinkReviewerUtils.queryParam('period')
  if (periodId) {
    try {
      var periodData = await Promise.all([FacultyLinkReviewerApi.listEvaluationPeriods(), FacultyLinkReviewerApi.listEvaluationActivities()])
      var period = periodData[0].find(function (p) { return p.id === periodId })
      var assigned = periodData[1].some(function (a) { return a.periodId === periodId && a.facultyId === facultyId })
      if (!assigned || !FacultyLinkEvaluationPeriods.permitted(period, 'reviewer')) {
        el.innerHTML = '<h1 class="admin-page-title">Assessment unavailable</h1><p class="admin-page-desc">' +
          FacultyLinkPeriodUI.esc(assigned ? FacultyLinkPeriodUI.accessMessage(period, 'reviewer') : 'This activity is not assigned to you for the selected period.') +
          '</p><a href="evaluation-schedule.html" class="fl-btn fl-btn--primary">Back to Evaluation Schedule</a>'
        return
      }
    } catch (_) {
      el.innerHTML = '<p class="admin-empty">Unable to check evaluation access. <a href="evaluation-schedule.html">Return to Evaluation Schedule</a></p>'
      return
    }
  }
  FacultyLinkReviewerApi.getKraAssessment(facultyId).then(function (data) {
    if (!data) {
      el.innerHTML = '<p class="admin-empty">Faculty not found.</p><a href="assigned-faculty.html">Back to Assigned Faculty</a>'
      return
    }
    if (!data.kras.length) {
      el.innerHTML = '<p class="admin-empty">No KRA configuration available.</p><a href="assigned-faculty.html">Back to Assigned Faculty</a>'
      return
    }
    function renderIndicator(ind) {
      var sem =
        ind.semesters &&
        ind.semesters
          .map(function (s) {
            return (
              '<tr><td>' +
              s.term +
              '</td><td>' +
              s.rating +
              '</td><td>' +
              (s.duplicate ? 'Possible duplicate (mock)' : '—') +
              '</td></tr>'
            )
          })
          .join('')

      return (
        '<details open><summary>' +
        ind.code +
        ' — ' +
        ind.title +
        '</summary>' +
        '<div style="padding:8px 0 16px 8px">' +
        '<p><strong>Evidence:</strong> ' +
        (ind.evidence ? ind.evidence.join(', ') : '—') +
        '</p>' +
        (sem
          ? '<p><strong>Semester records (illustrative):</strong></p><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Term</th><th>Rating</th><th>Duplicate warning</th></tr></thead><tbody>' +
            sem +
            '</tbody></table></div>'
          : '<p class="admin-empty-hint">No semester records available for this faculty member.</p>') +
        '<p><strong>Submitted documents (sample data):</strong></p>' +
        (ind.documents.length
          ? '<ul>' + ind.documents.map(function (doc) {
              return '<li><a href="document-detail.html?id=' + encodeURIComponent(doc.id) + (periodId ? '&amp;period=' + encodeURIComponent(periodId) : '') + '">' +
                doc.title + '</a> — ' + doc.status + '</li>'
            }).join('') + '</ul>'
          : '<p class="admin-empty-hint">No sample documents available for this faculty member.</p>') +
        '<p><strong>Aggregated indicator score:</strong> ' +
        (ind.aggregatedScore || 'Not Yet Calculated') +
        '</p>' +
        (ind.validation ? '<p class="reviewer-note">' + ind.validation + '</p>' : '') +
        '</div></details>'
      )
    }

    function renderCriterion(c) {
      var inds = c.indicators.map(renderIndicator).join('')
      return (
        '<details><summary>Criterion ' +
        c.code +
        ' — ' +
        c.title +
        '</summary><div class="reviewer-kra-tree">' +
        inds +
        '</div></details>'
      )
    }

    var tabs = data.kras
      .map(function (k, i) {
        return (
          '<button type="button" class="admin-tab' +
          (i === 0 ? ' is-active' : '') +
          '" data-kra="' +
          k.id +
          '">' +
          k.title.split('—')[0].trim() +
          '</button>'
        )
      })
      .join('')

    function renderKra(kra) {
      return (
        '<h2 style="margin:0;padding:16px 20px;border-bottom:1px solid var(--fl-border)">' +
        kra.title +
        '</h2><div style="padding:16px 20px">' +
        kra.criteria.map(renderCriterion).join('') +
        '</div>'
      )
    }

    el.innerHTML =
      '<h1 class="admin-page-title">KRA Assessment</h1>' +
      '<p class="admin-page-desc">' +
      data.facultyName +
      ' — hierarchy: KRA → Criterion → Indicator → Documents → Validation → Scoring. SET/SEF appear under KRA I, Criterion A (not separate modules).</p>' +
      '<div class="admin-tabs" id="kra-tabs">' +
      tabs +
      '</div>' +
      '<div class="admin-panel" id="kra-panel"></div>'

    var panel = document.getElementById('kra-panel')
    panel.innerHTML = renderKra(data.kras[0])
    document.getElementById('kra-tabs').addEventListener('click', function (e) {
      var btn = e.target.closest('[data-kra]')
      if (!btn) return
      document.querySelectorAll('.admin-tab').forEach(function (t) {
        t.classList.remove('is-active')
      })
      btn.classList.add('is-active')
      var kra = data.kras.find(function (k) {
        return k.id === btn.getAttribute('data-kra')
      })
      if (kra) panel.innerHTML = renderKra(kra)
    })
  })
}
