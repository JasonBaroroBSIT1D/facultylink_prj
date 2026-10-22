// Run with: node --test admin_reviewer_web/tests/frontend-regressions.test.js
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const { test } = require('node:test')

const root = path.resolve(__dirname, '..')
const source = (file) => fs.readFileSync(path.join(root, file), 'utf8')
const flush = () => new Promise((resolve) => setImmediate(resolve))

// Small event/HTML test double: exercises the existing page functions without
// adding a DOM framework. Browser layout and native form validation are not tested.
class Element {
  constructor(attributes = {}) {
    this.attributes = attributes
    this.innerHTML = ''
    this.listeners = {}
    this.children = new Map()
    this.classList = { add() {}, remove() {} }
    this.style = {}
  }
  addEventListener(event, handler) { this.listeners[event] = handler }
  getAttribute(name) { return this.attributes[name] }
  querySelector(selector) {
    if (!this.children.has(selector)) this.children.set(selector, new Element())
    return this.children.get(selector)
  }
  querySelectorAll(selector) {
    const found = []
    for (const tag of this.innerHTML.matchAll(/<button\b([^>]*)>/g)) {
      const attributes = Object.fromEntries([...tag[1].matchAll(/([\w-]+)="([^"]*)"/g)].map((m) => [m[1], m[2]]))
      if ((attributes.class || '').split(' ').includes(selector.slice(1))) found.push(new Element(attributes))
    }
    this.children.set(selector, found)
    return found
  }
  remove() { this.removed = true }
}

function runtime(storage = new Map(), search = '') {
  const elements = new Map()
  const document = {
    currentScript: { src: 'http://localhost/js/mock/evaluationScheduleStore.js' },
    addEventListener() {}, removeEventListener() {},
    body: { appendChild(element) { document.modal = element } },
    createElement: () => new Element(),
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, new Element())
      return elements.get(id)
    },
    querySelectorAll: () => [],
  }
  const context = vm.createContext({
    document, URL, URLSearchParams, addEventListener() {}, location: { search },
    setTimeout: () => 1, clearTimeout() {},
    fetch: async () => ({ ok: true, json: async () => JSON.parse(source('assets/data/evaluation-periods.json')) }),
    localStorage: { getItem: (key) => storage.get(key) || null, setItem: (key, value) => storage.set(key, value) },
    FormData: class { constructor(form) { this.values = form.values } get(key) { return this.values[key] } },
    alert() {}, confirm: () => true,
  })
  context.window = context
  context.FacultyLinkMockAuth = { loadSession: () => ({ reviewerId: 'R-01' }) }
  context.run = (file) => vm.runInContext(source(file), context, { filename: file })
  for (const file of ['js/kraStructure.js', 'js/mock/adminMockData.js', 'js/mock/reviewerMockData.js',
    'js/mock/evaluationScheduleStore.js', 'js/evaluation-period-ui.js', 'js/api/adminApi.js', 'js/api/reviewerApi.js', 'js/reviewer/utils.js']) context.run(file)
  return context
}

test('every reviewer dashboard document resolves to matching detail content', async () => {
  const app = runtime()
  for (const item of (await app.FacultyLinkReviewerApi.getDashboard()).attention) {
    const doc = await app.FacultyLinkReviewerApi.getDocument(item.id)
    assert.ok(doc, item.id)
    assert.equal(doc.title, item.title)
    assert.equal(doc.faculty, item.faculty)
    assert.equal(doc.reviewStatus, item.status)
  }
  app.location.search = '?id=DOC-8804'
  app.run('js/reviewer/pages/document-detail.js')
  const el = new Element()
  app.ReviewerPageInit(el, { statusBadge: (status) => status })
  await flush()
  assert.match(el.innerHTML, /Elena V\. Cruz/)
  assert.match(el.innerHTML, /Rejected/)
  assert.match(el.innerHTML, /Text extraction failed/)
  assert.doesNotMatch(el.innerHTML, /Document not found/)
  assert.equal(await app.FacultyLinkReviewerApi.getDocument('missing'), null)
})

test('KRA records and linked documents stay with their faculty, including empty records', async () => {
  const app = runtime()
  const api = app.FacultyLinkReviewerApi
  for (const faculty of await api.listAssignedFaculty()) {
    const assessment = await api.getKraAssessment(faculty.id)
    assert.equal(assessment.facultyName, faculty.name)
    assert.equal(assessment.facultyId, faculty.id)
    const indicators = assessment.kras.flatMap((k) => k.criteria.flatMap((c) => c.indicators))
    const docs = indicators.flatMap((i) => i.documents)
    assert.equal(docs.length, app.FacultyLinkReviewerMock.documents.filter((d) => d.facultyId === faculty.id).length)
    for (const doc of docs) assert.equal((await api.getDocument(doc.id)).facultyId, faculty.id)
    if (faculty.id !== 'F-001') assert.ok(indicators.every((i) => !i.semesters?.length))
  }
  const reyes = await api.getKraAssessment('F-001')
  reyes.kras[0].criteria[0].indicators[0].semesters[0].term = 'Changed in caller'
  assert.equal((await api.getKraAssessment('F-001')).kras[0].criteria[0].indicators[0].semesters[0].term, '1st Sem AY 2024–2025')
  assert.equal(await api.getKraAssessment('missing'), null)
  assert.equal(await api.getKraAssessment('toString'), null)
  const overview = await api.getFacultyOverview('F-002')
  assert.deepEqual(Array.from(overview.kraSummary, (k) => k.docs), [1, 0, 0, 0])
})

test('KRA page renders the selected faculty, working document targets, tabs and unknown-ID state', async () => {
  const app = runtime(new Map(), '?faculty=F-002')
  app.run('js/reviewer/pages/kra-assessment.js')
  const el = new Element()
  app.ReviewerPageInit(el)
  await flush()
  assert.match(el.innerHTML, /Juan Miguel Santos/)
  assert.doesNotMatch(el.innerHTML, /Maria Clara Reyes/)
  const panel = app.document.getElementById('kra-panel')
  assert.match(panel.innerHTML, /document-detail.html\?id=DOC-8819/)
  assert.doesNotMatch(panel.innerHTML, /AY 2024–2025|DOC-8821/)
  const button = new Element({ 'data-kra': 'kra2' })
  app.document.getElementById('kra-tabs').listeners.click({ target: { closest: () => button } })
  assert.match(panel.innerHTML, /KRA II/)
  assert.doesNotMatch(panel.innerHTML, /DOC-8819/)
  app.location.search = '?faculty=missing'
  app.ReviewerPageInit(el)
  await flush()
  assert.match(el.innerHTML, /Faculty not found/)
  assert.match(el.innerHTML, /assigned-faculty.html/)
})

test('all local HTML references, sidebar targets and frontend JavaScript syntax are valid', () => {
  function walk(dir) {
    return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
      const file = path.join(dir, entry.name)
      return entry.isDirectory() ? walk(file) : [file]
    })
  }
  for (const file of walk(root).filter((file) => file.endsWith('.html'))) {
    for (const match of fs.readFileSync(file, 'utf8').matchAll(/(?:href|src)\s*=\s*["']([^"']+)["']/g)) {
      if (/^(?:[a-z]+:|\/\/|#)/i.test(match[1])) continue
      const target = match[1].split(/[?#]/)[0]
      assert.ok(fs.existsSync(path.resolve(path.dirname(file), target)), `${file}: ${target}`)
    }
  }
  for (const file of walk(path.join(root, 'js'))) if (file.endsWith('.js')) new vm.Script(fs.readFileSync(file, 'utf8'), { filename: file })
  const app = runtime()
  for (const role of ['admin', 'reviewer']) {
    app.run(`js/${role}/nav-config.js`)
    for (const section of app[role === 'admin' ? 'FacultyLinkAdminNav' : 'FacultyLinkReviewerNav']) {
      for (const item of section.items) assert.ok(fs.existsSync(path.join(root, role, item.href)))
    }
  }
})
