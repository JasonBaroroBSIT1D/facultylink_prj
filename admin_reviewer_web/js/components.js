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

  global.FacultyLinkUI = {
    logoMarkup: logoMarkup,
    mountLogos: mountLogos,
    assetPrefix: assetPrefix,
  }
})(window)
