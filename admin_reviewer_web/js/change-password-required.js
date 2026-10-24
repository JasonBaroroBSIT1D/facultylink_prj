document.addEventListener('DOMContentLoaded', function () {
  if (window.FacultyLinkUI) FacultyLinkUI.mountLogos()

  var form = document.getElementById('change-required-form')
  var errorEl = document.getElementById('change-error')
  var successEl = document.getElementById('change-success')
  var submitBtn = document.getElementById('change-submit')

  function apiOrigin() {
    if (window.FacultyLinkApiOrigin) return window.FacultyLinkApiOrigin()
    return window.location.origin
  }

  fetch(apiOrigin() + '/api/v1/auth/me', { credentials: 'include', headers: { Accept: 'application/json' } })
    .then(function (r) {
      return r.json().then(function (body) {
        return { ok: r.ok, body: body }
      })
    })
    .then(function (result) {
      if (!result.ok || !result.body.must_change_password) {
        window.location.href = 'login.html'
      }
    })

  if (!form) return

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
    if (form.new_password.value !== form.confirm_password.value) {
      if (errorEl) {
        errorEl.textContent = 'New passwords do not match.'
        errorEl.hidden = false
      }
      return
    }
    if (submitBtn) {
      submitBtn.disabled = true
      submitBtn.textContent = 'Updating…'
    }
    fetch(apiOrigin() + '/api/v1/auth/complete-mandatory-password', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        temporary_password: form.temporary_password.value,
        new_password: form.new_password.value,
        confirm_password: form.confirm_password.value,
      }),
    })
      .then(function (r) {
        return r.json().then(function (body) {
          return { ok: r.ok, body: body }
        })
      })
      .then(function (result) {
        if (submitBtn) {
          submitBtn.disabled = false
          submitBtn.textContent = 'Update Password'
        }
        if (!result.ok) {
          if (errorEl) {
            errorEl.textContent = result.body.message || 'Unable to update password.'
            errorEl.hidden = false
          }
          return
        }
        if (form) form.hidden = true
        if (successEl) {
          successEl.textContent = result.body.message || 'Password updated.'
          successEl.hidden = false
        }
        setTimeout(function () {
          window.location.href = 'login.html'
        }, 1500)
      })
      .catch(function () {
        if (submitBtn) {
          submitBtn.disabled = false
          submitBtn.textContent = 'Update Password'
        }
        if (errorEl) {
          errorEl.textContent = 'Unable to reach the FacultyLink API.'
          errorEl.hidden = false
        }
      })
  })
})
