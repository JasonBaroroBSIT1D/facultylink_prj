window.AdminPageInit = function (el) {
  FacultyLinkAdminApi.getSettings().then(function (s) {
    el.innerHTML =
      '<h1 class="admin-page-title">Account &amp; System Settings</h1>' +
      '<p class="admin-page-desc">Institution profile and integration preferences — saves require Flask API.</p>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>General</h2></div>' +
      '<div class="admin-form-grid">' +
      '<div class="admin-form-field"><label>Institution name</label><input type="text" value="' +
      s.institutionName +
      '" readonly /></div>' +
      '<div class="admin-form-field"><label>Admin email</label><input type="email" value="' +
      s.adminEmail +
      '" readonly /></div>' +
      '<div class="admin-form-field"><label>Timezone</label><select disabled><option>' +
      s.timezone +
      '</option></select></div>' +
      '<div class="admin-form-field"><label>OCR language (Tesseract)</label><input type="text" value="' +
      s.ocrLanguage +
      '" readonly /></div>' +
      '<div class="admin-form-field"><label>Auto-approve valid documents</label><select disabled><option>' +
      (s.autoApproveEnabled ? 'Enabled' : 'Disabled') +
      '</option></select></div>' +
      '</div></div>' +
      '<button type="button" class="fl-btn fl-btn--primary" disabled>Save changes (API)</button>'
  })
}
