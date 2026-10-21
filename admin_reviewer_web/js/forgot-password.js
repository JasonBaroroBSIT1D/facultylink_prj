document.addEventListener('DOMContentLoaded', function () {
  if (window.FacultyLinkUI) {
    FacultyLinkUI.mountLogos()
  }

  var yearEl = document.getElementById('fl-copyright-year')
  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear())
  }

  var form = document.getElementById('forgot-form')
  var errorEl = document.getElementById('forgot-error')
  var successEl = document.getElementById('forgot-success')
  var submitBtn = document.getElementById('forgot-submit')

  if (!form) return

  function isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault()
    if (errorEl) {
      errorEl.hidden = true
      errorEl.textContent = ''
    }
    if (successEl) {
      successEl.hidden = true
      successEl.textContent = ''
    }

    var email = form.email.value.trim()
    if (!isValidEmail(email)) {
      if (errorEl) {
        errorEl.textContent = 'Enter a valid email address (example: name@university.edu.ph).'
        errorEl.hidden = false
      }
      return
    }

    if (submitBtn) {
      submitBtn.disabled = true
      submitBtn.textContent = 'Submitting…'
    }

    window.setTimeout(function () {
      if (submitBtn) {
        submitBtn.disabled = false
        submitBtn.textContent = 'Submit Request'
      }
      if (successEl) {
        successEl.innerHTML =
          '<strong>Mock mode:</strong> Recovery request recorded for <strong>' +
          email +
          '</strong>. No email was sent—this UI is ready for a future secure password-reset API.'
        successEl.hidden = false
      }
      form.reset()
    }, 650)
  })
})
