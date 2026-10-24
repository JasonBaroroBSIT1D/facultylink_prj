document.addEventListener('DOMContentLoaded', function () {
  if (window.FacultyLinkUI) FacultyLinkUI.mountLogos()

  var state = { step: 1, email: '', resetGrant: '', resendCooldown: 0, resendTimer: null }

  var stepEmail = document.getElementById('step-email')
  var stepOtp = document.getElementById('step-otp')
  var stepReset = document.getElementById('step-reset')
  var stepSuccess = document.getElementById('step-success')
  var errorEl = document.getElementById('forgot-error')
  var formEmail = document.getElementById('forgot-form-email')
  var formOtp = document.getElementById('forgot-form-otp')
  var formReset = document.getElementById('forgot-form-reset')
  var resendBtn = document.getElementById('otp-resend')
  var resendHint = document.getElementById('otp-resend-hint')

  function apiOrigin() {
    if (window.FacultyLinkApiOrigin) return window.FacultyLinkApiOrigin()
    return window.location.origin
  }

  function showStep(n) {
    state.step = n
    if (stepEmail) stepEmail.hidden = n !== 1
    if (stepOtp) stepOtp.hidden = n !== 2
    if (stepReset) stepReset.hidden = n !== 3
    if (stepSuccess) stepSuccess.hidden = n !== 4
    if (errorEl) {
      errorEl.hidden = true
      errorEl.textContent = ''
    }
  }

  function showError(msg) {
    if (errorEl) {
      errorEl.textContent = msg
      errorEl.hidden = false
    }
  }

  function startResendCooldown(seconds) {
    state.resendCooldown = seconds
    if (resendBtn) resendBtn.disabled = true
    if (state.resendTimer) clearInterval(state.resendTimer)
    state.resendTimer = setInterval(function () {
      state.resendCooldown -= 1
      if (resendHint) {
        resendHint.textContent =
          state.resendCooldown > 0
            ? 'Resend available in ' + state.resendCooldown + 's'
            : 'Codes expire after 5 minutes.'
      }
      if (state.resendCooldown <= 0) {
        clearInterval(state.resendTimer)
        if (resendBtn) resendBtn.disabled = false
      }
    }, 1000)
  }

  showStep(1)

  if (formEmail) {
    formEmail.addEventListener('submit', function (e) {
      e.preventDefault()
      var email = formEmail.email.value.trim()
      var btn = formEmail.querySelector('button[type="submit"]')
      if (btn) {
        btn.disabled = true
        btn.textContent = 'Sending…'
      }
      fetch(apiOrigin() + '/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ email: email }),
      })
        .then(function (r) {
          return r.json().then(function (body) {
            return { ok: r.ok, body: body }
          })
        })
        .then(function (result) {
          if (btn) {
            btn.disabled = false
            btn.textContent = 'Send Verification Code'
          }
          state.email = email
          showStep(2)
          startResendCooldown(60)
          if (result.body.email_delivery && result.body.email_delivery.sent === false) {
            showError('Email delivery failed. Try again later or contact your administrator.')
          }
        })
        .catch(function () {
          if (btn) {
            btn.disabled = false
            btn.textContent = 'Send Verification Code'
          }
          showError('Unable to reach the FacultyLink API.')
        })
    })
  }

  if (formOtp) {
    formOtp.addEventListener('submit', function (e) {
      e.preventDefault()
      var otp = formOtp.otp.value.trim()
      var btn = formOtp.querySelector('button[type="submit"]')
      if (btn) {
        btn.disabled = true
        btn.textContent = 'Verifying…'
      }
      fetch(apiOrigin() + '/api/v1/auth/forgot-password/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ email: state.email, otp: otp }),
      })
        .then(function (r) {
          return r.json().then(function (body) {
            return { ok: r.ok, body: body }
          })
        })
        .then(function (result) {
          if (btn) {
            btn.disabled = false
            btn.textContent = 'Verify Code'
          }
          if (!result.ok) {
            showError(result.body.message || 'Invalid verification code.')
            return
          }
          state.resetGrant = result.body.reset_grant
          showStep(3)
        })
        .catch(function () {
          if (btn) {
            btn.disabled = false
            btn.textContent = 'Verify Code'
          }
          showError('Unable to reach the FacultyLink API.')
        })
    })
  }

  if (resendBtn) {
    resendBtn.addEventListener('click', function () {
      if (state.resendCooldown > 0) return
      resendBtn.disabled = true
      fetch(apiOrigin() + '/api/v1/auth/forgot-password/resend-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ email: state.email }),
      })
        .then(function (r) {
          return r.json().then(function (body) {
            return { ok: r.ok, body: body }
          })
        })
        .then(function (result) {
          if (!result.ok) {
            showError(result.body.message || 'Unable to resend code.')
            resendBtn.disabled = false
            return
          }
          startResendCooldown(60)
        })
        .catch(function () {
          showError('Unable to reach the FacultyLink API.')
          resendBtn.disabled = false
        })
    })
  }

  if (formReset) {
    formReset.addEventListener('submit', function (e) {
      e.preventDefault()
      if (formReset.new_password.value !== formReset.confirm_password.value) {
        showError('Passwords do not match.')
        return
      }
      var btn = formReset.querySelector('button[type="submit"]')
      if (btn) {
        btn.disabled = true
        btn.textContent = 'Saving…'
      }
      fetch(apiOrigin() + '/api/v1/auth/forgot-password/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          email: state.email,
          reset_grant: state.resetGrant,
          new_password: formReset.new_password.value,
          confirm_password: formReset.confirm_password.value,
        }),
      })
        .then(function (r) {
          return r.json().then(function (body) {
            return { ok: r.ok, body: body }
          })
        })
        .then(function (result) {
          if (btn) {
            btn.disabled = false
            btn.textContent = 'Save New Password'
          }
          if (!result.ok) {
            showError(result.body.message || 'Unable to save password.')
            return
          }
          showStep(4)
        })
        .catch(function () {
          if (btn) {
            btn.disabled = false
            btn.textContent = 'Save New Password'
          }
          showError('Unable to reach the FacultyLink API.')
        })
    })
  }
})
