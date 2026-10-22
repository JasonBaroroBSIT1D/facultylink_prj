(function (global) {
  function assetPrefix() {
    var path = window.location.pathname.replace(/\\/g, '/')
    if (path.indexOf('/admin/') !== -1 || path.indexOf('/reviewer/') !== -1) {
      return '../'
    }
    return ''
  }

  var LOGO_SRC = assetPrefix() + 'assets/images/facultylink-logo.jpg'
  var HOME_HREF = assetPrefix() + 'index.html'

  function wordmarkMarkup(variant) {
    var light = variant === 'light'
    return (
      '<div class="fl-wordmark' +
      (light ? ' fl-wordmark--light' : '') +
      '">' +
      '<span class="fl-wordmark__name"><span class="fl-wordmark__faculty">Faculty</span><span class="fl-wordmark__link">Link</span></span>' +
      '<span class="fl-wordmark__tag">Self-Assessment &amp; Rank Simulation</span></div>'
    )
  }

  function logoMarkup(options) {
    var size = (options && options.size) || 'md'
    var variant = (options && options.variant) || 'dark'
    var mode = (options && options.mode) || 'auto'
    var showText = !options || options.showText !== false
    var emblemOnly = options && options.emblemOnly

    if (mode === 'nav' || mode === 'lockup') {
      return (
        '<a class="fl-brand-lockup fl-brand-lockup--' +
        size +
        (variant === 'light' ? ' fl-brand-lockup--light' : '') +
        '" href="' +
        HOME_HREF +
        '">' +
        '<img class="fl-logo__img fl-logo__img--emblem" src="' +
        LOGO_SRC +
        '" alt="" width="40" height="40" />' +
        wordmarkMarkup(variant) +
        '</a>'
      )
    }

    if (mode === 'form') {
      return (
        '<div class="fl-logo fl-logo--form">' +
        '<img class="fl-logo__img fl-logo__img--emblem" src="' +
        LOGO_SRC +
        '" alt="FacultyLink" width="36" height="36" />' +
        wordmarkMarkup('dark') +
        '</div>'
      )
    }

    var imgClass = 'fl-logo__img'
    if (emblemOnly || mode === 'emblem') {
      imgClass += ' fl-logo__img--emblem'
    }

    var img =
      '<img class="' +
      imgClass +
      '" src="' +
      LOGO_SRC +
      '" alt="FacultyLink" width="240" height="240" />'

    var text =
      showText && !emblemOnly && mode !== 'emblem'
        ? wordmarkMarkup(variant)
        : ''

    return (
      '<div class="fl-logo fl-logo--' +
      size +
      ' fl-logo--' +
      variant +
      '">' +
      img +
      text +
      '</div>'
    )
  }

  function mountLogos() {
    document.querySelectorAll('[data-fl-logo]').forEach(function (el) {
      el.outerHTML = logoMarkup({
        size: el.getAttribute('data-size') || 'md',
        variant: el.getAttribute('data-variant') || 'dark',
        mode: el.getAttribute('data-logo-mode') || 'auto',
        showText: el.getAttribute('data-show-text') !== 'false',
        emblemOnly: el.getAttribute('data-emblem-only') === 'true',
      })
    })
  }

  // Both portal shells use the same breakpoint and drawer behavior.
  function initPortalNavigation() {
    var sidebar = document.getElementById('admin-sidebar')
    var menu = document.getElementById('admin-menu-btn')
    var close = document.getElementById('admin-menu-close')
    var overlay = document.getElementById('admin-overlay')
    var main = document.querySelector('.admin-main')
    var compact = global.matchMedia('(max-width: 1024px)')
    var opened = false

    function setOpen(next, restoreFocus) {
      var wasOpen = opened
      opened = compact.matches && next
      sidebar.classList.toggle('is-open', opened)
      overlay.classList.toggle('is-visible', opened)
      document.body.classList.toggle('admin-drawer-open', opened)
      menu.setAttribute('aria-expanded', String(opened))
      main.inert = opened
      sidebar.inert = compact.matches && !opened
      if (compact.matches) {
        sidebar.setAttribute('role', 'dialog')
        sidebar.setAttribute('aria-modal', 'true')
        sidebar.setAttribute('aria-hidden', String(!opened))
      } else {
        sidebar.removeAttribute('role')
        sidebar.removeAttribute('aria-modal')
        sidebar.removeAttribute('aria-hidden')
      }
      if (opened) close.focus()
      else if (restoreFocus && wasOpen && compact.matches) menu.focus()
    }

    menu.addEventListener('click', function () { setOpen(!opened, true) })
    close.addEventListener('click', function () { setOpen(false, true) })
    overlay.addEventListener('click', function () { setOpen(false, true) })
    sidebar.addEventListener('click', function (event) {
      if (event.target.closest('a[href]')) setOpen(false, true)
    })
    document.addEventListener('keydown', function (event) {
      if (!opened) return
      if (event.key === 'Escape') {
        event.preventDefault()
        setOpen(false, true)
      } else if (event.key === 'Tab') {
        var items = sidebar.querySelectorAll('a[href], button:not(:disabled), [tabindex="0"]')
        var first = items[0]
        var last = items[items.length - 1]
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault()
          last.focus()
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault()
          first.focus()
        }
      }
    })
    compact.addEventListener('change', function () {
      var focusedInSidebar = sidebar.contains(document.activeElement)
      var focusedOnMenu = document.activeElement === menu
      setOpen(false, false)
      if (compact.matches && focusedInSidebar) menu.focus()
      else if (!compact.matches && (focusedInSidebar || focusedOnMenu)) {
        var activeLink = sidebar.querySelector('.is-active') || sidebar.querySelector('a[href]')
        if (activeLink) activeLink.focus()
      }
    })
    setOpen(false, false)
  }

  global.FacultyLinkUI = {
    logoMarkup: logoMarkup,
    mountLogos: mountLogos,
    assetPrefix: assetPrefix,
    initPortalNavigation: initPortalNavigation,
  }
})(window)
