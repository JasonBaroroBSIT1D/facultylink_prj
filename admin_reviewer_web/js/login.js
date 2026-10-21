document.addEventListener('DOMContentLoaded', function () {
  if (window.FacultyLinkUI) {
    FacultyLinkUI.mountLogos()
  }

  var yearEl = document.getElementById('fl-copyright-year')
  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear())
  }

  var form = document.getElementById('login-form')
  var errorEl = document.getElementById('login-error')
  var submitBtn = document.getElementById('login-submit')
  var passwordInput = document.getElementById('password')
  var toggleBtn = document.getElementById('password-toggle')

  if (toggleBtn && passwordInput) {
    toggleBtn.addEventListener('click', function () {
      var show = passwordInput.type === 'password'
      passwordInput.type = show ? 'text' : 'password'
      toggleBtn.setAttribute('aria-label', show ? 'Hide password' : 'Show password')
    })
  }

  if (!form) return

  form.addEventListener('submit', function (e) {
    e.preventDefault()
    if (errorEl) {
      errorEl.hidden = true
      errorEl.textContent = ''
    }

    var email = form.email.value
    var password = form.password.value

    if (submitBtn) {
      submitBtn.disabled = true
      submitBtn.textContent = 'Signing in…'
    }

    FacultyLinkMockAuth.signIn(email, password).then(function (result) {
      if (submitBtn) {
        submitBtn.disabled = false
        submitBtn.textContent = 'Sign In'
      }

      if (!result.ok) {
        if (errorEl) {
          errorEl.textContent = result.message
          errorEl.hidden = false
        }
        return
      }

      FacultyLinkMockAuth.saveSession({
        email: email.trim().toLowerCase(),
        role: result.role,
        displayName: result.displayName,
      })

      if (result.role === 'admin') {
        window.location.href = 'admin/dashboard.html'
      } else {
        window.location.href = 'reviewer/dashboard.html'
      }
    })
  })
})
