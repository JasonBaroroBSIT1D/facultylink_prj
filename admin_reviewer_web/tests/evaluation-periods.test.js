const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const crypto = require('node:crypto')
const { test } = require('node:test')
const root = path.resolve(__dirname, '..')
const seed = JSON.parse(fs.readFileSync(path.join(root, 'assets/data/evaluation-periods.json'), 'utf8'))
const flush = () => new Promise((resolve) => setImmediate(resolve))

// Event/markup checks; native browser layout and form controls need browser QA.
class Element {
  constructor(attrs = {}) {
    this.attrs = attrs; this.listeners = {}; this.nodes = new Map()
    this.elements = { namedItem: (key) => this.querySelector(`[name="${key}"]`) || this.querySelector(`#error-${key}`) }
    this.classList = { add() {}, remove() {} }
    this._html = ''
    this._form = null
  }
  set innerHTML(html) {
    this._html = html
    if (html.includes('id="schedule-form"')) {
      this._form = new Element()
      this._form.values = {}
      this._form.elements = { namedItem: (key) => ({ setAttribute() {}, removeAttribute() {}, focus() {} }) }
      this._form.querySelectorAll = (sel) => (sel === '.ep-error' ? [] : [])
      this.nodes.set('#schedule-form', this._form)
    }
  }
  get innerHTML() { return this._html }
  addEventListener(name, fn) { this.listeners[name] = fn }
  setAttribute(name, value) { this.attrs[name] = value }
  getAttribute(name) { return this.attrs[name] }
  hasAttribute(name) { return Object.hasOwn(this.attrs, name) }
  removeAttribute(name) { delete this.attrs[name] }
  querySelector(key) {
    if (this.nodes.has(key)) return this.nodes.get(key)
    const node = new Element()
    node.textContent = ''
    this.nodes.set(key, node)
    return node
  }
  querySelectorAll(sel) {
    if (sel === '.ep-error') return [...this.nodes.values()].filter((n) => n.textContent != null)
    if (sel === '[aria-invalid]') return []
    return []
  }
  querySelectorAll() { return [] }
  focus() {}
  showModal() { this.open = true }
  close() { this.open = false; this.listeners.close?.() }
  remove() { this.removed = true }
}

function app({ storage = new Map(), role = 'admin', now = '2026-10-22T04:00:00Z', search = '' } = {}) {
  let clock = Date.parse(now)
  class TestDate extends Date { constructor(...args) { super(...(args.length ? args : [clock])) } static now() { return clock } }
  const events = {}
  const document = {
    currentScript: { src: 'http://localhost/js/mock/evaluationScheduleStore.js' },
    activeElement: null, hidden: false,
    createElement: () => new Element(),
    body: { appendChild(el) { document.modal = el } },
    addEventListener() {}, removeEventListener() {}, querySelectorAll: () => [],
    getElementById(id) { return document.bodyElement.querySelector(id) }, bodyElement: new Element(),
  }
  const context = vm.createContext({
    document, Date: TestDate, URL, URLSearchParams, crypto,
    location: { search }, setTimeout: () => 1, clearTimeout() {},
    addEventListener: (name, fn) => { events[name] = fn },
    fetch: async () => ({ ok: true, json: async () => JSON.parse(JSON.stringify(seed)) }),
    localStorage: { getItem: (key) => storage.get(key) || null, setItem: (key, value) => storage.set(key, value) },
    FormData: class { constructor(form) { this.values = form.values } get(key) { return this.values[key] ?? '' } has(key) { return !!this.values[key] } },
    FacultyLinkMockAuth: { loadSession: () => ({ role, reviewerId: 'R-01' }) },
  })
  context.window = context
  context.run = (file) => vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context, { filename: file })
  context.setClock = (time) => { clock = Date.parse(time) }
  context.events = events
  for (const file of ['js/mock/evaluationScheduleStore.js', 'js/evaluation-period-ui.js', 'js/kraStructure.js',
    'js/mock/adminMockData.js', 'js/mock/reviewerMockData.js', 'js/api/adminApi.js', 'js/api/reviewerApi.js', 'js/reviewer/utils.js']) context.run(file)
  return context
}

const entry = () => ({ name: 'Second Semester AY 2026–2027', academicYear: 'AY 2026–2027', semester: 'Second Semester',
  opensAt: '2027-01-01T08:00:00+08:00', closesAt: '2027-01-31T23:59:00+08:00', description: 'Demo', submissionEnabled: true, reviewEnabled: true })

test('shared JSON loads and Manila status boundaries are independent of host timezone', async () => {
  const ctx = app(); const store = ctx.FacultyLinkEvaluationPeriods
  await store.ready()
  const p = store.list().find((p) => p.id === 'EP-2026-11')
  assert.equal(store.status(p, Date.parse('2026-10-31T23:59:59Z')), 'Upcoming')
  assert.equal(store.status(p, Date.parse('2026-11-01T00:00:00Z')), 'Open')
  assert.equal(store.status(p, Date.parse('2026-11-30T15:59:00Z')), 'Closed')
  assert.equal(ctx.FacultyLinkPeriodUI.format(p.opensAt), 'Nov 1, 2026 • 8:00 AM')
  assert.equal(ctx.FacultyLinkPeriodUI.format(p.closesAt), 'Nov 30, 2026 • 11:59 PM')
  assert.equal(store.focus(store.list()).id, 'EP-2026-10')
})

test('admin create/edit persists the same period to reviewer tabs and read-only API has no mutations', async () => {
  const storage = new Map(); const admin = app({ storage }); const reviewer = app({ storage, role: 'reviewer' })
  await admin.FacultyLinkEvaluationPeriods.ready(); await reviewer.FacultyLinkEvaluationPeriods.ready()
  const created = await admin.FacultyLinkAdminApi.saveEvaluationPeriod(entry())
  assert.equal((await reviewer.FacultyLinkReviewerApi.listEvaluationPeriods()).find((p) => p.id === created.id).name, entry().name)
  await admin.FacultyLinkAdminApi.saveEvaluationPeriod({ ...entry(), name: 'Revised semester window' }, created.id)
  let changes = 0
  reviewer.FacultyLinkEvaluationPeriods.subscribe(() => changes++)
  reviewer.events.storage({ key: 'facultylink_evaluation_periods_v1' })
  assert.equal(changes, 1)
  const reload = app({ storage, role: 'reviewer' }); await reload.FacultyLinkEvaluationPeriods.ready()
  assert.equal(reload.FacultyLinkEvaluationPeriods.list().find((p) => p.id === created.id).name, 'Revised semester window')
  assert.equal(reviewer.FacultyLinkReviewerApi.saveEvaluationPeriod, undefined)
  await assert.rejects(reviewer.FacultyLinkAdminApi.saveEvaluationPeriod(entry()), /Administrator access/)
})

test('missing fields, impossible dates, reversed ranges and duplicate periods are rejected', async () => {
  const ctx = app(); const store = ctx.FacultyLinkEvaluationPeriods; await store.ready()
  for (const change of [{ name: ' ' }, { semester: '' }, { academicYear: '' }, { opensAt: '' },
    { opensAt: '2027-02-30T08:00:00+08:00' }, { closesAt: entry().opensAt }, { closesAt: '2026-01-01T08:00:00+08:00' }]) {
    assert.throws(() => store.write({ ...entry(), ...change }), /Check the evaluation/)
  }
  store.write(entry())
  assert.throws(() => store.write({ ...entry(), name: '  SECOND SEMESTER AY 2026–2027  ' }), /Check the evaluation/)
  assert.throws(() => store.write({ ...entry(), name: 'Different name' }), /Check the evaluation/)
})

test('overlap requires acknowledgement; adjacent windows are permitted', async () => {
  const ctx = app(); const store = ctx.FacultyLinkEvaluationPeriods; await store.ready()
  const overlapping = { ...entry(), opensAt: '2026-10-25T08:00:00+08:00' }
  assert.throws(() => store.write(overlapping), /Check the evaluation/)
  assert.ok(store.write(overlapping, null, true).id)
  const adjacent = { ...entry(), name: 'Next window', opensAt: entry().closesAt, closesAt: '2027-02-28T23:59:00+08:00' }
  assert.equal(store.validate(adjacent).overlaps.length, 0)
  assert.ok(store.write(adjacent).id)
})

test('early close changes the closing instant and immediately removes submission/review permission', async () => {
  const ctx = app(); const store = ctx.FacultyLinkEvaluationPeriods; await store.ready()
  const closed = await ctx.FacultyLinkAdminApi.closeEvaluationPeriod('EP-2026-10')
  assert.equal(closed.closesAt, '2026-10-22T12:00:00+08:00')
  assert.equal(store.status(closed), 'Closed')
  assert.equal(store.permitted(closed, 'faculty'), false)
  assert.equal(store.permitted(closed, 'reviewer'), false)
  assert.throws(() => store.close('EP-2026-11'), /Only an open/)
  const open = { ...entry(), opensAt: '2026-10-01T08:00:00+08:00', reviewEnabled: false, submissionEnabled: false }
  assert.equal(store.permitted(open, 'reviewer'), false)
  assert.equal(store.permitted(open, 'faculty'), false)
})

test('unavailable storage retains temporary demo state and surfaces its limitation', async () => {
  const ctx = app(); ctx.localStorage = { getItem() { throw Error('blocked') }, setItem() { throw Error('blocked') } }
  const store = ctx.FacultyLinkEvaluationPeriods; await store.ready(); const p = store.write(entry())
  assert.equal(store.isPersistent(), false)
  assert.ok(store.list().some((row) => row.id === p.id))
})

function click(el, action, id = '') {
  el.listeners.click({ target: { closest: () => new Element({ 'data-action': action, 'data-id': id }) } })
}
test('Admin UI shows period settings, validates dates, and saves edits', async () => {
  const ctx = app(); ctx.run('js/admin/pages/evaluation-schedule.js'); const el = new Element(); ctx.AdminPageInit(el); await flush()
  assert.match(el.innerHTML, /Evaluation Period Settings/)
  assert.match(el.innerHTML, /Edit Schedule/)
  assert.doesNotMatch(el.innerHTML, /sched-cal|Upcoming Periods|ep-summary/)
  click(el, 'edit'); await flush()
  let form = el.querySelector('#schedule-form')
  form.values = { academicYear: 'AY 2026–2027', openingDate: '2027-01-01', openingTime: '08:00', closingDate: '2026-12-31', closingTime: '23:59' }
  form.listeners.submit({ preventDefault() {}, target: form }); await flush()
  assert.match(el.querySelector('#error-closesAt').textContent, /later than opening/)
  assert.match(el.innerHTML, /Save Evaluation Schedule/)
})

test('Reviewer UI is read-only and shows evaluation period fields', async () => {
  const ctx = app({ role: 'reviewer' }); ctx.run('js/reviewer/pages/evaluation-schedule.js'); const el = new Element(); ctx.ReviewerPageInit(el); await flush()
  assert.match(el.innerHTML, /Evaluation cycle \/ academic year/)
  assert.match(el.innerHTML, /Evaluation status/)
  assert.doesNotMatch(el.innerHTML, /Save Evaluation Schedule|data-action="edit"|sched-cal|Assigned activities/)
  ctx.setClock('2026-12-01T00:00:00Z'); ctx.ReviewerPageInit(el); await flush()
  assert.match(el.innerHTML, /Closed/)
})

test('period-scoped direct assessment links reject closed and unassigned activities', async () => {
  const ctx = app({ role: 'reviewer', search: '?faculty=F-004&period=EP-2026-11' })
  ctx.run('js/reviewer/pages/kra-assessment.js'); const el = new Element()
  await ctx.ReviewerPageInit(el)
  assert.match(el.innerHTML, /not yet open/)
  ctx.location.search = '?faculty=F-003&period=EP-2026-10'
  await ctx.ReviewerPageInit(el)
  assert.match(el.innerHTML, /not assigned to you/)
})

test('document decisions cannot bypass the period window via an unscoped URL', async () => {
  const ctx = app({ role: 'reviewer', search: '?id=DOC-8819' })
  ctx.run('js/reviewer/pages/document-detail.js'); const el = new Element()
  ctx.ReviewerPageInit(el, { statusBadge: (s) => s }); await flush()
  assert.equal(ctx.document.getElementById('btn-verify').disabled, false)
  ctx.setClock('2026-12-01T00:00:00Z')
  ctx.document.getElementById('btn-verify').listeners.click()
  assert.equal(ctx.document.getElementById('btn-verify').disabled, true)
  assert.match(ctx.document.getElementById('period-review-access').textContent, /closed/)
  assert.notEqual(ctx.document.getElementById('review-modal').open, true)
})
