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
})
