window.AdminPageInit = function (el) {
  FacultyLinkAdminApi.listNotifications().then(function (items) {
    var list = items
      .map(function (n) {
        return (
          '<li style="padding:16px 20px;border-bottom:1px solid var(--fl-border);' +
          (n.unread ? 'background:rgba(40,120,240,0.04)' : '') +
          '"><strong>' +
          n.title +
          '</strong><br /><span style="color:var(--fl-text-muted);font-size:0.88rem">' +
          n.body +
          '</span><br /><time style="font-size:0.75rem;color:var(--fl-text-muted)">' +
          n.time +
          '</time></li>'
        )
      })
      .join('')

    el.innerHTML =
      '<h1 class="admin-page-title">Notifications</h1>' +
      '<p class="admin-page-desc">System alerts for administrators (mock feed).</p>' +
      '<div class="admin-panel"><ul style="list-style:none;margin:0;padding:0">' +
      list +
      '</ul></div>'
  })
}
