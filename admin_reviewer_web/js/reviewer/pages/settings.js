window.ReviewerPageInit = function (el) {
  FacultyLinkReviewerApi.getSettings().then(function (s) {
    el.innerHTML =
      '<h1 class="admin-page-title">Account Settings</h1>' +
      '<p class="admin-page-desc">Reviewer profile and notification preferences — save requires Flask API.</p>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Profile</h2></div>' +
      '<div class="admin-form-grid">' +
      '<div class="admin-form-field"><label>Name</label><input type="text" value="' +
      s.name +
      '" readonly /></div>' +
      '<div class="admin-form-field"><label>Email</label><input type="email" value="' +
      s.email +
      '" readonly /></div>' +
      '<div class="admin-form-field"><label>Department</label><input type="text" value="' +
      s.department +
      '" readonly /></div>' +
      '</div></div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Notifications</h2></div>' +
      '<div style="padding:20px;font-size:0.9rem">' +
      '<label><input type="checkbox" disabled checked /> Verification requests (mock)</label><br /><br />' +
      '<label><input type="checkbox" disabled checked /> Revision submissions (mock)</label>' +
      '</div></div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Password</h2></div>' +
      '<div style="padding:20px"><button type="button" class="fl-btn fl-btn--ghost" disabled>Change password (API)</button></div></div>'
  })
}
