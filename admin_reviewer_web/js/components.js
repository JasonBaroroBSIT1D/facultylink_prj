(function (global) {
  var LOGO_SRC = 'assets/images/facultylink-logo.jpg'

  function logoMarkup(options) {
    var size = (options && options.size) || 'md'
    var variant = (options && options.variant) || 'dark'
    var showText = !options || options.showText !== false
    var emblemOnly = options && options.emblemOnly

    var imgClass = 'fl-logo__img'
    if (emblemOnly) {
      imgClass += ' fl-logo__img--emblem'
    }

    var img =
      '<img class="' +
      imgClass +
      '" src="' +
      LOGO_SRC +
      '" alt="FacultyLink — Faculty Self-Assessment and Rank Simulation System" width="240" height="240" />'

    var text = showText && !emblemOnly
      ? '<div class="fl-logo__text"><span class="fl-logo__name">FacultyLink</span>' +
        '<span class="fl-logo__tagline">Faculty Self-Assessment and Rank Simulation System</span></div>'
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
        showText: el.getAttribute('data-show-text') !== 'false',
        emblemOnly: el.getAttribute('data-emblem-only') === 'true',
      })
    })
  }

  global.FacultyLinkUI = {
    logoMarkup: logoMarkup,
    mountLogos: mountLogos,
  }
})(window)
