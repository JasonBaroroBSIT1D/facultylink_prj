(function (global) {
  var store = global.FacultyLinkEvaluationPeriods
  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    })
  }
  function format(value) {
    var date = new Date(value)
    return new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Manila', month: 'short', day: 'numeric', year: 'numeric' }).format(date) +
      ' • ' + new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit', hour12: true }).format(date)
  }
  function remaining(period) {
    var state = store.status(period)
    if (state === 'Closed') return 'Evaluation window has ended'
    var minutes = Math.max(1, Math.ceil((store.instant(state === 'Open' ? period.closesAt : period.opensAt) - Date.now()) / 60000))
    var days = Math.floor(minutes / 1440)
    var hours = Math.floor((minutes % 1440) / 60)
    var text = days ? days + 'd ' + hours + 'h' : hours ? hours + 'h ' + (minutes % 60) + 'm' : minutes + 'm'
    return state === 'Open' ? text + ' remaining' : 'Opens in ' + text
  }
  function badge(period) {
    var state = store.status(period)
    return '<span class="ep-status ep-status--' + state.toLowerCase() + '"><span aria-hidden="true"></span>' + state + '</span>'
  }
  function action(label, name, id, primary) {
    return '<button type="button" class="fl-btn ' + (primary ? 'fl-btn--primary' : 'fl-btn--ghost') +
      '" data-action="' + name + '" data-id="' + esc(id) + '">' + label + '</button>'
  }
  function feature(period, admin) {
    if (!period) return '<section class="ep-empty"><h2>No evaluation periods yet</h2><p>' +
      (admin ? 'Create a period to set the submission and review window.' : 'Your administrator has not configured an evaluation period.') + '</p></section>'
    var state = store.status(period)
    var progress = Math.max(0, Math.min(100, 100 * (Date.now() - store.instant(period.opensAt)) / (store.instant(period.closesAt) - store.instant(period.opensAt))))
    return '<section class="ep-feature"><div class="ep-feature__intro"><div class="ep-eyebrow">' +
      (state === 'Open' ? 'Active evaluation period' : state === 'Upcoming' ? 'Next evaluation period' : 'Most recent evaluation period') + '</div>' +
      '<h2>' + esc(period.name) + '</h2><p class="ep-meta">' + esc(period.academicYear) + ' / ' + esc(period.semester) + '</p>' +
      '<p class="ep-description">' + esc(period.description || 'Faculty self-assessment and advisory rank simulation.') + '</p>' +
      (admin ? '<div class="ep-actions">' + action('Edit Period', 'edit', period.id, true) + action('View Details', 'details', period.id) +
        (state === 'Open' ? action('Close Period', 'close', period.id) : '') + '</div>' : '') +
      '</div><div class="ep-feature__window"><div class="ep-window-head">' + badge(period) + '<span>' + remaining(period) + '</span></div>' +
      '<dl class="ep-dates"><div><dt>Opening</dt><dd>' + format(period.opensAt) + '</dd></div><div><dt>Closing</dt><dd>' + format(period.closesAt) + '</dd></div></dl>' +
      '<div class="ep-progress" role="progressbar" aria-label="Evaluation window elapsed" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + Math.round(progress) + '"><span style="width:' + progress + '%"></span></div>' +
      '<p class="ep-window-note">All dates and times are Asia/Manila (UTC+8).</p></div></section>'
  }
  function accessMessage(period, role) {
    if (!period) return 'No evaluation period is configured.'
    var state = store.status(period)
    if (state === 'Upcoming') return 'This period is not yet open. Access begins ' + format(period.opensAt) + '.'
    if (state === 'Closed') return 'This period closed ' + format(period.closesAt) + '. Evaluation activities are read-only.'
    return store.permitted(period, role) ? 'Evaluation activities are available until ' + format(period.closesAt) + '.' : 'Your administrator has paused ' + (role === 'faculty' ? 'submissions' : 'reviewer activities') + ' for this period.'
  }
  function dialog(title, body) {
    var previous = document.activeElement
    var node = document.createElement('dialog')
    node.className = 'ep-dialog'
    node.innerHTML = '<div class="ep-dialog__head"><div><span class="ep-eyebrow">Evaluation periods</span><h2 id="ep-dialog-title">' + esc(title) +
      '</h2></div><button type="button" class="ep-dialog__close" data-dismiss aria-label="Close dialog">×</button></div>' + body
    node.setAttribute('aria-labelledby', 'ep-dialog-title')
    node.addEventListener('click', function (e) { if (e.target === node || e.target.closest('[data-dismiss]')) node.close() })
    node.addEventListener('close', function () { node.remove(); if (previous && previous.isConnected) previous.focus() })
    document.body.appendChild(node)
    node.showModal()
    return node
  }
  function watch(render) {
    var timer
    function tick() {
      clearTimeout(timer)
      render()
      var now = Date.now()
      var delay = 30000
      store.list().forEach(function (p) {
        ;[p.opensAt, p.closesAt].forEach(function (date) {
          var delta = store.instant(date) - now
          if (delta > 0) delay = Math.min(delay, delta + 20)
        })
      })
      timer = setTimeout(tick, delay)
    }
    var unsubscribe = store.subscribe(tick)
    var visible = function () { if (!document.hidden) tick() }
    document.addEventListener('visibilitychange', visible)
    global.addEventListener('pagehide', function () { clearTimeout(timer); unsubscribe(); document.removeEventListener('visibilitychange', visible) }, { once: true })
    tick()
  }
  global.FacultyLinkPeriodUI = { esc: esc, format: format, remaining: remaining, badge: badge, action: action, feature: feature, accessMessage: accessMessage, dialog: dialog, watch: watch }
})(window)
