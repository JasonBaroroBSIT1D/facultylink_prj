window.ReviewerPageInit = function (el, h) {
  var id = FacultyLinkReviewerUtils.queryParam('id') || 'DOC-8819'
  FacultyLinkReviewerApi.getDocument(id).then(function (doc) {
    if (!doc) {
      el.innerHTML = '<p class="admin-empty">Document not found.</p>'
      return
    }

    var checks = doc.validation.checks
      .map(function (c) {
        return (
          '<li>' +
          FacultyLinkReviewerUtils.checkIcon(c.result) +
          '<div><strong>' +
          c.name +
          '</strong><br /><span style="color:var(--fl-text-muted)">' +
          c.detail +
          '</span></div></li>'
        )
      })
      .join('')

    var fields = doc.ocr.fields
      .map(function (f) {
        return '<tr><td>' + f.label + '</td><td>' + f.value + '</td><td>' + f.confidence + '</td></tr>'
      })
      .join('')

    el.innerHTML =
      '<a href="document-review.html" class="fl-btn fl-btn--ghost" style="margin-bottom:16px;padding:8px 14px">← Back to queue</a>' +
      '<h1 class="admin-page-title">' +
      doc.title +
      '</h1>' +
      '<p class="admin-page-desc">' +
      doc.faculty +
      ' · ' +
      doc.kra +
      ' → Criterion ' +
      doc.criterion +
      ' → ' +
      doc.indicator +
      ' · ' +
      h.statusBadge(doc.reviewStatus) +
      '</p>' +
      (doc.reviewStatus === 'System Approved'
        ? '<p class="reviewer-note">This document satisfied all mandatory validation rules and was <strong>System Approved</strong>. Reviewer inspection is optional unless an override is authorized.</p>'
        : '') +
      (doc.validation.needsVerificationReason
        ? '<p class="reviewer-note"><strong>Why verification is required:</strong> ' +
          doc.validation.needsVerificationReason +
          '</p>'
        : '') +
      '<div class="reviewer-doc-layout">' +
      '<section class="admin-panel"><div class="admin-panel__head"><h2>A. Original document</h2>' +
      '<a href="' +
      doc.previewUrl +
      '" target="_blank" rel="noopener" class="fl-btn fl-btn--ghost" style="padding:6px 12px;font-size:0.8rem">Download</a></div>' +
      '<div class="reviewer-preview"><div class="reviewer-preview__toolbar">' +
      '<button type="button" class="fl-btn fl-btn--ghost" style="padding:4px 10px;font-size:0.75rem" id="zoom-out">−</button>' +
      '<button type="button" class="fl-btn fl-btn--ghost" style="padding:4px 10px;font-size:0.75rem" id="zoom-in">+</button>' +
      '</div><div class="reviewer-preview__frame" id="preview-frame">' +
      '<iframe id="pdf-frame" src="' +
      doc.previewUrl +
      '" title="Document preview"></iframe></div></div></section>' +
      '<section class="admin-panel"><div class="admin-panel__head"><h2>B. OCR extraction (mock)</h2></div>' +
      '<p style="padding:0 20px;font-size:0.88rem;color:var(--fl-text-muted)">' +
      doc.ocr.text +
      '</p>' +
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Field</th><th>Value</th><th>Confidence</th></tr></thead><tbody>' +
      fields +
      '</tbody></table></div>' +
      (doc.ocr.gaps.length
        ? '<p style="padding:12px 20px;font-size:0.85rem"><strong>Uncertain:</strong> ' +
          doc.ocr.gaps.join('; ') +
          '</p>'
        : '') +
      '</section></div>' +
      '<div class="reviewer-split-panels">' +
      '<section class="admin-panel"><div class="admin-panel__head"><h2>C. Rule-based validation</h2></div>' +
      '<p style="padding:12px 20px 0;margin:0;font-size:0.88rem">' +
      doc.validation.overall +
      '</p>' +
      '<ul class="reviewer-checklist" style="padding:12px 20px 20px">' +
      checks +
      '</ul></section>' +
      '<section class="admin-panel"><div class="admin-panel__head"><h2>D. Reviewer verification</h2></div>' +
      '<div style="padding:20px"><label class="admin-form-field"><span style="font-weight:600;font-size:0.85rem">Comments</span>' +
      '<textarea id="review-comments" rows="4" style="width:100%;margin-top:8px;padding:10px;border-radius:8px;border:1.5px solid var(--fl-border)"></textarea></label>' +
      '<p style="font-size:0.8rem;color:var(--fl-text-muted)">' +
      doc.reviewer.note +
      '</p>' +
      '<p class="reviewer-note" id="period-review-access" role="status"></p>' +
      '<div class="admin-toolbar" style="margin-top:16px">' +
      '<button type="button" class="fl-btn fl-btn--primary" id="btn-verify">Confirm verification (mock)</button>' +
      '<button type="button" class="fl-btn fl-btn--ghost" id="btn-revision">Request revision (mock)</button>' +
      '<button type="button" class="fl-btn fl-btn--ghost" id="btn-reject">Reject (mock)</button>' +
      '</div></div></section></div>' +
      '<dialog class="reviewer-modal" id="review-modal"><div class="reviewer-modal__inner">' +
      '<h3 id="modal-title">Mock action</h3><p id="modal-body"></p>' +
      '<div class="reviewer-modal__actions"><button type="button" class="fl-btn fl-btn--ghost" id="modal-close">Close</button></div></div></dialog>'

    var scale = 1
    var frame = document.getElementById('pdf-frame')
    document.getElementById('zoom-in').addEventListener('click', function () {
      scale = Math.min(1.5, scale + 0.1)
      frame.style.transform = 'scale(' + scale + ')'
      frame.style.transformOrigin = 'top left'
    })
    document.getElementById('zoom-out').addEventListener('click', function () {
      scale = Math.max(0.7, scale - 0.1)
      frame.style.transform = 'scale(' + scale + ')'
    })

    var modal = document.getElementById('review-modal')
    var periodId = FacultyLinkReviewerUtils.queryParam('period')
    var assignedActivities = []
    var accessNote = document.getElementById('period-review-access')
    function selectedPeriod() {
      var rows = FacultyLinkEvaluationPeriods.list().filter(function (p) {
        return (!periodId || p.id === periodId) && assignedActivities.some(function (a) { return a.periodId === p.id })
      })
      return FacultyLinkEvaluationPeriods.focus(rows.filter(function (p) { return FacultyLinkEvaluationPeriods.permitted(p, 'reviewer') })) || FacultyLinkEvaluationPeriods.focus(rows)
    }
    function setAccess(allowed, message) {
      ;['btn-verify', 'btn-revision', 'btn-reject', 'review-comments'].forEach(function (id) {
        document.getElementById(id).disabled = !allowed
      })
      accessNote.textContent = message
    }
    function refreshAccess() {
      var period = selectedPeriod()
      setAccess(FacultyLinkEvaluationPeriods.permitted(period, 'reviewer'), period ? FacultyLinkPeriodUI.accessMessage(period, 'reviewer') :
        'Read-only: no evaluation activity is assigned to you for this document in the selected period.')
    }
    setAccess(false, 'Checking evaluation-period access…')
    Promise.all([FacultyLinkReviewerApi.listEvaluationPeriods(), FacultyLinkReviewerApi.listEvaluationActivities()]).then(function (data) {
      assignedActivities = data[1].filter(function (a) { return a.facultyId === doc.facultyId })
      FacultyLinkPeriodUI.watch(refreshAccess)
    }).catch(function () { setAccess(false, 'Evaluation access is unavailable. Return to Evaluation Schedule and try again.') })
    function showMock(title, body) {
      if (!FacultyLinkEvaluationPeriods.permitted(selectedPeriod(), 'reviewer')) { refreshAccess(); return }
      document.getElementById('modal-title').textContent = title
      document.getElementById('modal-body').textContent = body
      modal.showModal()
    }
    document.getElementById('modal-close').addEventListener('click', function () {
      modal.close()
    })
    document.getElementById('btn-verify').addEventListener('click', function () {
      showMock(
        'Mock — not saved',
        'Verification recorded in UI only. Flask API required to persist review decisions.',
      )
    })
    document.getElementById('btn-revision').addEventListener('click', function () {
      showMock('Mock — revision request', 'Would notify faculty via backend when connected.')
    })
    document.getElementById('btn-reject').addEventListener('click', function () {
      showMock('Mock — reject', 'Authorized rejection would be audit-logged by the backend.')
    })
  })
}
