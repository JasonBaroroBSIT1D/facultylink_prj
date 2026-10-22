/** Browser-only evaluation periods. The JSON seed is also bundled by Flutter. */
(function (global) {
  var key = 'facultylink_evaluation_periods_v1'
  var seedUrl = new URL('../../assets/data/evaluation-periods.json', document.currentScript.src).href
  var periods = []
  var loading
  var storageAvailable = true
  var listeners = []
  function copy(value) { return JSON.parse(JSON.stringify(value)) }
  function instant(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$/.test(value)) return NaN
    var time = Date.parse(value)
    if (!Number.isFinite(time)) return NaN
    return new Date(time + 8 * 3600000).toISOString().slice(0, 19) === value.slice(0, 19) ? time : NaN
  }
  function status(period, now) {
    now = now == null ? Date.now() : Number(now)
    return now < instant(period.opensAt) ? 'Upcoming' : now >= instant(period.closesAt) ? 'Closed' : 'Open'
  }
  function normalize(text) { return String(text || '').trim().toLowerCase().replace(/\s+/g, ' ') }
  function validate(entry, id, rows) {
    var errors = {}
    ;['name', 'academicYear', 'semester', 'opensAt', 'closesAt'].forEach(function (field) {
      if (typeof entry[field] !== 'string' || !entry[field].trim()) errors[field] = 'This field is required.'
    })
    var start = instant(entry.opensAt)
    var end = instant(entry.closesAt)
    if (!Number.isFinite(start)) errors.opensAt = 'Enter a valid opening date and time (Asia/Manila).'
    if (!Number.isFinite(end)) errors.closesAt = 'Enter a valid closing date and time (Asia/Manila).'
    if (Number.isFinite(start) && Number.isFinite(end) && end <= start) errors.closesAt = 'Closing must be later than opening.'
    var others = (rows || periods).filter(function (p) { return p.id !== id })
    if (others.some(function (p) {
      return normalize(p.name) === normalize(entry.name) ||
        (normalize(p.academicYear) === normalize(entry.academicYear) && p.semester === entry.semester &&
          p.opensAt === entry.opensAt && p.closesAt === entry.closesAt)
    })) errors.name = 'A matching evaluation period already exists. Edit that period instead.'
    return { errors: errors, overlaps: others.filter(function (p) { return start < instant(p.closesAt) && end > instant(p.opensAt) }) }
  }
  function validRows(rows) {
    return Array.isArray(rows) && new Set(rows.map(function (p) { return p && p.id })).size === rows.length &&
      rows.every(function (p) {
        return p && typeof p.id === 'string' && p.id && typeof p.description === 'string' &&
          typeof p.submissionEnabled === 'boolean' && typeof p.reviewEnabled === 'boolean' &&
          !Object.keys(validate(p, p.id, []).errors).length
      })
  }
  function readStored() {
    try {
      var saved = JSON.parse(global.localStorage.getItem(key))
      if (saved && saved.version === 1 && validRows(saved.periods)) periods = saved.periods
    } catch (_) { storageAvailable = false }
  }
  function emit() { listeners.forEach(function (listener) { listener() }) }
  function save() {
    try { global.localStorage.setItem(key, JSON.stringify({ version: 1, timezone: 'Asia/Manila', periods: periods })) }
    catch (_) { storageAvailable = false }
    emit()
  }
  function replaceAll(rows) {
    if (!validRows(rows)) throw new Error('Invalid evaluation-period data from server.')
    periods = copy(rows)
    emit()
  }
  function usingServerSource() {
    return !!global.__facultylinkPeriodsFromServer
  }
  function ready() {
    if (!loading) loading = fetch(seedUrl).then(function (response) {
      if (!response.ok) throw new Error('Unable to load evaluation periods.')
      return response.json()
    }).then(function (data) {
      if (data.timezone !== 'Asia/Manila' || !validRows(data.periods)) throw new Error('Invalid evaluation-period data.')
      periods = copy(data.periods)
      readStored()
    }).catch(function (error) { loading = null; throw error })
    return loading
  }
  function list() {
    readStored()
    return copy(periods).sort(function (a, b) { return instant(a.opensAt) - instant(b.opensAt) })
  }
  function focus(rows, now) {
    var open = rows.filter(function (p) { return status(p, now) === 'Open' }).sort(function (a, b) { return instant(a.closesAt) - instant(b.closesAt) })
    var upcoming = rows.filter(function (p) { return status(p, now) === 'Upcoming' }).sort(function (a, b) { return instant(a.opensAt) - instant(b.opensAt) })
    var closed = rows.filter(function (p) { return status(p, now) === 'Closed' }).sort(function (a, b) { return instant(b.closesAt) - instant(a.closesAt) })
    return open[0] || upcoming[0] || closed[0] || null
  }
  function permitted(period, role, now) {
    return !!period && status(period, now) === 'Open' && (role === 'faculty' ? period.submissionEnabled : period.reviewEnabled)
  }
  function write(entry, id, acknowledgeOverlap) {
    readStored()
    if (id && !periods.some(function (p) { return p.id === id })) throw new Error('This period no longer exists.')
    var result = validate(entry, id)
    if (Object.keys(result.errors).length || (result.overlaps.length && !acknowledgeOverlap)) {
      var error = new Error('Check the evaluation period details.')
      error.validation = result
      throw error
    }
    var period = {
      id: id || 'EP-' + global.crypto.randomUUID(), name: entry.name.trim(), academicYear: entry.academicYear.trim(),
      semester: entry.semester.trim(), opensAt: entry.opensAt, closesAt: entry.closesAt,
      description: String(entry.description || '').trim(), submissionEnabled: entry.submissionEnabled !== false,
      reviewEnabled: entry.reviewEnabled !== false,
    }
    if (id) periods = periods.map(function (p) { return p.id === id ? period : p })
    else periods.push(period)
    save()
    return copy(period)
  }
  function close(id, now) {
    readStored()
    now = now == null ? Date.now() : Number(now)
    var period = periods.find(function (p) { return p.id === id })
    if (!period || status(period, now) !== 'Open') throw new Error('Only an open period can be closed early.')
    if (Math.floor(now / 1000) * 1000 <= instant(period.opensAt)) throw new Error('The period just opened. Please wait a second before closing it.')
    period.closesAt = new Date(Math.floor(now / 1000) * 1000 + 8 * 3600000).toISOString().slice(0, 19) + '+08:00'
    save()
    return copy(period)
  }
  global.addEventListener('storage', function (event) { if (event.key === key) { readStored(); emit() } })
  global.FacultyLinkEvaluationPeriods = {
    ready: ready, list: list, status: status, instant: instant, focus: focus, permitted: permitted,
    validate: validate, write: write, close: close, replaceAll: replaceAll, usingServerSource: usingServerSource,
    subscribe: function (fn) { listeners.push(fn); return function () { listeners = listeners.filter(function (f) { return f !== fn }) } },
    isPersistent: function () { return usingServerSource() || storageAvailable },
  }
})(window)
