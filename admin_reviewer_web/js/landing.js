document.addEventListener('DOMContentLoaded', function () {
  if (window.FacultyLinkUI) {
    FacultyLinkUI.mountLogos()
  }

  var yearEl = document.getElementById('fl-copyright-year')
  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear())
  }

  var menuBtn = document.querySelector('.landing-nav__menu')
  var navLinks = document.querySelector('.landing-nav__links')
  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', function () {
      var open = navLinks.classList.toggle('is-open')
      menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false')
    })
  }

  var sectionLinks = document.querySelectorAll('[data-nav-section]')
  var sections = ['home', 'features', 'about']
    .map(function (id) {
      return document.getElementById(id)
    })
    .filter(Boolean)

  function setActive(sectionId) {
    sectionLinks.forEach(function (link) {
      link.classList.toggle('is-active', link.getAttribute('data-nav-section') === sectionId)
    })
  }

  if (sections.length && sectionLinks.length) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            setActive(entry.target.id)
          }
        })
      },
      { rootMargin: '-40% 0px -50% 0px', threshold: 0.01 }
    )
    sections.forEach(function (section) {
      observer.observe(section)
    })
  }
})
