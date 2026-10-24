// Event-level regression checks; these do not simulate browser layout/scrolling.
// Run: node --test admin_reviewer_web/tests/*.test.js
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const { test } = require('node:test')
const root = path.resolve(__dirname, '..')
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8')

function portal(width = 390, role = 'admin', page = 'dashboard') {
  const document = { activeElement: null }
  class Element {
    constructor() {
      this.attributes = {}
      this.listeners = {}
      this.inert = false
      const classes = new Set()
      this.classList = {
        add: (name) => classes.add(name),
        contains: (name) => classes.has(name),
        toggle: (name, on) => on ? classes.add(name) : classes.delete(name),
      }
    }
    setAttribute(key, value) { this.attributes[key] = value }
    getAttribute(key) { return this.attributes[key] }
    removeAttribute(key) { delete this.attributes[key] }
    addEventListener(type, callback) { this.listeners[type] = callback }
    fire(type, values = {}) {
      const event = { target: this, prevented: false, preventDefault() { this.prevented = true }, ...values }
      this.listeners[type]?.(event)
      return event
    }
    focus() { document.activeElement = this }
  }
  const body = new Element()
  body.setAttribute(`data-${role}-page`, page)
  const sidebar = new Element(), menu = new Element(), close = new Element()
  const overlay = new Element(), main = new Element(), brand = new Element()
  const nav = new Element(), active = new Element(), last = new Element()
  const focusable = [brand, close, nav, active, last]
  sidebar.contains = (element) => focusable.includes(element)
  sidebar.querySelectorAll = () => focusable
  sidebar.querySelector = () => active
  const elements = new Map([
    ['admin-sidebar', sidebar], ['admin-menu-btn', menu], ['admin-menu-close', close],
    ['admin-overlay', overlay],
  ])
  document.body = body
  document.querySelector = () => main
  document.querySelectorAll = () => []
  document.getElementById = (id) => {
    if (!elements.has(id)) elements.set(id, new Element())
    return elements.get(id)
  }
  const keyEvents = new Element()
  document.addEventListener = keyEvents.addEventListener.bind(keyEvents)
  const media = new Element()
  const app = vm.createContext({
    document,
    location: { pathname: `/${role}/${page}.html` },
    matchMedia(query) {
      media.matches = width <= Number(query.match(/\d+/)[0])
      return media
    },
    FacultyLinkMockAuth: {
      loadSession: () => ({ displayName: 'Test FacultyLink User', email: 'test@example.com' }),
      clearSession() {},
    },
  })
  app.window = app
  const run = (file) => vm.runInContext(read(file), app, { filename: file })
  run('js/components.js')
  run('js/shared/portalNav.js')
  run(`js/${role}/nav-config.js`)
  run(`js/${role}/shell.js`)
  return {
    app, document, body, sidebar, menu, close, overlay, main, brand, nav, active, last,
    key: (key, shiftKey = false) => keyEvents.fire('keydown', { key, shiftKey }),
    resize(nextWidth) { media.matches = nextWidth <= 1024; media.fire('change') },
  }
}

for (const role of ['admin', 'reviewer']) {
  test(`${role}: drawer opens, locks the background and closes via every control`, () => {
    const p = portal(390, role)
    assert.equal(p.sidebar.inert, true)
    assert.equal(p.sidebar.getAttribute('aria-hidden'), 'true')
    assert.equal(p.menu.getAttribute('aria-expanded'), 'false')
    const dismiss = [
      () => p.close.fire('click'),
      () => p.overlay.fire('click'),
      () => p.key('Escape'),
      () => p.sidebar.fire('click', { target: { closest: () => p.last } }),
    ]
    for (const action of dismiss) {
      p.menu.fire('click')
      assert.equal(p.sidebar.inert, false)
      assert.equal(p.sidebar.getAttribute('role'), 'dialog')
      assert.equal(p.sidebar.getAttribute('aria-modal'), 'true')
      assert.equal(p.menu.getAttribute('aria-expanded'), 'true')
      assert.ok(p.sidebar.classList.contains('is-open'))
      assert.ok(p.overlay.classList.contains('is-visible'))
      assert.ok(p.body.classList.contains('admin-drawer-open'))
      assert.equal(p.main.inert, true)
      assert.equal(p.document.activeElement, p.close)
      action()
      assert.equal(p.main.inert, false)
      assert.equal(p.sidebar.inert, true)
      assert.equal(p.document.activeElement, p.menu)
      assert.equal(p.menu.getAttribute('aria-expanded'), 'false')
      assert.equal(p.overlay.classList.contains('is-visible'), false)
      assert.equal(p.body.classList.contains('admin-drawer-open'), false)
    }
  })

  test(`${role}: keyboard focus wraps inside the drawer and normal keys are preserved`, () => {
    const p = portal(375, role)
    assert.equal(p.key('Escape').prevented, false)
    p.menu.fire('click')
    p.last.focus()
    assert.equal(p.key('Tab').prevented, true)
    assert.equal(p.document.activeElement, p.brand)
    assert.equal(p.key('Tab', true).prevented, true)
    assert.equal(p.document.activeElement, p.last)
    p.nav.focus()
    assert.equal(p.key('ArrowDown').prevented, false)
    assert.equal(p.key('Tab').prevented, false)
    assert.equal(p.key('Escape').prevented, true)
  })

  test(`${role}: resizing releases the scroll lock and prevents hidden focus`, () => {
    const p = portal(768, role)
    p.menu.fire('click')
    p.resize(1366)
    assert.equal(p.main.inert, false)
    assert.equal(p.sidebar.inert, false)
    assert.equal(p.sidebar.getAttribute('role'), undefined)
    assert.equal(p.sidebar.getAttribute('aria-hidden'), undefined)
    assert.equal(p.document.activeElement, p.active)
    assert.equal(p.body.classList.contains('admin-drawer-open'), false)
    p.resize(1024)
    assert.equal(p.sidebar.inert, true)
    assert.equal(p.document.activeElement, p.menu)
    p.resize(1920)
    assert.equal(p.document.activeElement, p.active)
  })

  test(`${role}: desktop mode leaves navigation available without a modal or background lock`, () => {
    for (const width of [1920, 1366, 1025]) {
      const p = portal(width, role)
      p.menu.fire('click') // Even a programmatic click cannot open a desktop overlay.
      assert.equal(p.sidebar.inert, false)
      assert.equal(p.main.inert, false)
      assert.equal(p.overlay.classList.contains('is-visible'), false)
    }
    for (const width of [1024, 768, 390, 375]) {
      const p = portal(width, role)
      p.menu.fire('click')
      assert.ok(p.sidebar.classList.contains('is-open'))
    }
  })

  test(`${role}: every page loads the shared shell and retains all navigation and active state`, () => {
    for (const file of fs.readdirSync(path.join(root, role)).filter((f) => f.endsWith('.html'))) {
      const html = read(`${role}/${file}`)
      const page = html.match(new RegExp(`data-${role}-page="([^"]+)"`))[1]
      assert.ok(html.includes(`../css/${role}-portal.css`), file)
      assert.ok(html.indexOf('../js/components.js') < html.indexOf(`../js/${role}/shell.js`), file)
      const p = portal(390, role, page)
      const markup = p.body.innerHTML
      const config = p.app[role === 'admin' ? 'FacultyLinkAdminNav' : 'FacultyLinkReviewerNav']
      const items = config.flatMap((section) => section.items)
      assert.equal([...markup.matchAll(/class="admin-nav-link(?:\s|")/g)].length, items.length, file)
      assert.equal([...markup.matchAll(/aria-current="page"/g)].length, 1, file)
      const active = items.find((item) => item.id === page)
      assert.ok(
        markup.includes(`class="admin-nav-link is-active" href="${active.href}"`) &&
          markup.includes(`aria-current="page"`),
        file
      )
      assert.ok(markup.includes('admin-nav-link__icon'), file)
      for (const item of items) assert.ok(fs.existsSync(path.join(root, role, item.href)), item.href)
      assert.match(markup, /id="admin-menu-btn"[^>]*aria-controls="admin-sidebar"/)
      assert.match(markup, /id="admin-menu-close"[^>]*aria-label="Close navigation"/)
    }
  })
}
