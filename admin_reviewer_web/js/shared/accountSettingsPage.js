/**
 * Shared Account Settings UI for Admin & Reviewer portals.
 */
(function (global) {
  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    })
  }

  function initials(name) {
    return (name || 'U')
      .split(/\s+/)
      .filter(Boolean)
      .map(function (p) {
        return p[0]
      })
      .slice(0, 2)
      .join('')
      .toUpperCase()
  }

  function iconUser() {
    return '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 12a4 4 0 100-8 4 4 0 000 8z" stroke="currentColor" stroke-width="1.8"/><path d="M4 20c0-3.3 3.6-5 8-5s8 1.7 8 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
  }

  function iconMail() {
    return '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 6h16v12H4V6z" stroke="currentColor" stroke-width="1.8"/><path d="M4 7l8 6 8-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
  }

  function iconBell() {
    return '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3a5 5 0 00-5 5v3.5L5 14v1h14v-1l-2-2.5V8a5 5 0 00-5-5z" stroke="currentColor" stroke-width="1.8"/><path d="M10 18a2 2 0 004 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
  }

  function iconLock() {
    return '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.8"/><path d="M8 11V8a4 4 0 118 0v3" stroke="currentColor" stroke-width="1.8"/></svg>'
  }

  function iconInfo() {
    return '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8"/><path d="M12 10v6M12 7h.01" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
  }

  function iconBuilding() {
    return '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 20h16M6 20V8l6-4 6 4v12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M10 12h4M10 16h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
  }

  function iconShield() {
    return '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z" stroke="currentColor" stroke-width="1.8"/></svg>'
  }

  function iconEye(open) {
    if (open) {
      return '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.8"/></svg>'
    }
    return '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3 3l18 18M10.5 10.7A3 3 0 0012 15a3 3 0 002.3-1M9.9 5.1A10.8 10.8 0 0112 5c6.5 0 10 7 10 7a18.4 18.4 0 01-4.2 5.1M6.4 6.4C3.6 8.4 2 12 2 12s3.5 7 10 7c1.1 0 2.1-.2 3-.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
  }

  function detailRow(iconSvg, label, value) {
    return (
      '<div class="rs-detail-row">' +
      '<div class="rs-detail-row__icon">' +
      iconSvg +
      '</div><div><span class="rs-detail-row__label">' +
      esc(label) +
      '</span><span class="rs-detail-row__value">' +
      esc(value) +
      '</span></div></div>'
    )
  }

  function passwordField(id, name, label, placeholder, autocomplete) {
    return (
      '<div class="rs-field"><label for="' +
      id +
      '">' +
      esc(label) +
      '</label><div class="rs-field__control">' +
      '<svg class="rs-field__lock" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.8"/><path d="M8 11V8a4 4 0 118 0v3" stroke="currentColor" stroke-width="1.8"/></svg>' +
      '<input id="' +
      id +
      '" name="' +
      name +
      '" type="password" autocomplete="' +
      autocomplete +
      '" required minlength="8" placeholder="' +
      esc(placeholder) +
      '" />' +
      '<button type="button" class="rs-field__toggle" data-toggle-for="' +
      id +
      '" aria-label="Show password">' +
      iconEye(false) +
      '</button></div></div>'
    )
  }

  function validatePasswordClient(password) {
    if (password.length < 8) return 'Password must be at least 8 characters.'
    if (!/[A-Za-z]/.test(password)) return 'Password must include at least one letter.'
    if (!/\d/.test(password)) return 'Password must include at least one number.'
    return ''
  }

  global.FacultyLinkAccountSettingsPage = {
    mount: function (el, options) {
      var state = { loading: true, error: '', notice: '', user: null, passwordBusy: false }
      var roleLabel = options.roleLabel || 'User'
      var requiredRole = options.requiredRole
      var loginPath = options.loginPath || '../login.html'

      function departmentFor(user) {
        if (typeof options.departmentFor === 'function') return options.departmentFor(user)
        var dept = user && user.department
        if (!dept || dept === '—' || dept === '-') return 'Not specified'
        return dept
      }

      function bindPasswordToggles(root) {
        root.querySelectorAll('[data-toggle-for]').forEach(function (btn) {
          btn.addEventListener('click', function () {
            var input = document.getElementById(btn.getAttribute('data-toggle-for'))
            if (!input) return
            var show = input.type === 'password'
            input.type = show ? 'text' : 'password'
            btn.innerHTML = iconEye(show)
            btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password')
          })
        })
      }

      function setPasswordError(message) {
        var errEl = document.getElementById('password-form-error')
        if (!errEl) return
        if (message) {
          errEl.textContent = message
          errEl.hidden = false
        } else {
          errEl.textContent = ''
          errEl.hidden = true
        }
      }

      function paint() {
        if (state.loading) {
          el.innerHTML =
            '<div class="rs-page"><header class="rs-page__head"><h1>Account Settings</h1>' +
            '<p role="status">Loading your account…</p></header>' +
            '<div class="rs-loading" aria-hidden="true"><div class="rs-loading__bar"></div>' +
            '<div class="rs-loading__bar rs-loading__bar--lg"></div></div></div>'
          return
        }
        if (state.error && !state.user) {
          el.innerHTML =
            '<div class="rs-page"><header class="rs-page__head"><h1>Account Settings</h1></header>' +
            '<p class="rs-alert rs-alert--error" role="alert">' +
            esc(state.error) +
            '</p><button type="button" class="fl-btn fl-btn--primary" id="settings-retry">Try again</button></div>'
          var retry = document.getElementById('settings-retry')
          if (retry) retry.addEventListener('click', loadProfile)
          return
        }

        var user = state.user
        el.innerHTML =
          '<div class="rs-page"><header class="rs-page__head"><h1>Account Settings</h1>' +
          '<p>Manage your profile, notification preferences, and account security.</p></header>' +
          (state.notice ? '<p class="rs-alert rs-alert--success" role="status">' + esc(state.notice) + '</p>' : '') +
          (state.error && state.user ? '<p class="rs-alert rs-alert--error" role="alert">' + esc(state.error) + '</p>' : '') +
          '<article class="rs-card"><header class="rs-card__head"><div class="rs-card__icon">' +
          iconUser() +
          '</div><div><h2>Profile Information</h2><p>Your account details are managed by your administrator.</p></div></header>' +
          '<div class="rs-card__body"><div class="rs-profile__grid"><aside class="rs-profile__aside">' +
          '<div class="rs-profile__avatar" aria-hidden="true">' +
          esc(initials(user.full_name)) +
          '</div><h3 class="rs-profile__name">' +
          esc(user.full_name) +
          '</h3><span class="rs-profile__badge">' +
          esc(roleLabel) +
          '</span><div class="rs-profile__email-row">' +
          iconMail() +
          '<span>' +
          esc(user.email) +
          '</span></div></aside><div class="rs-profile__details">' +
          detailRow(iconUser(), 'Full Name', user.full_name) +
          detailRow(iconMail(), 'Email Address', user.email) +
          detailRow(iconBuilding(), 'Department', departmentFor(user)) +
          detailRow(iconShield(), 'Role', roleLabel) +
          '</div></div><p class="rs-info-banner">' +
          iconInfo() +
          '<span>To update your profile information, please contact your system administrator.</span></p></div></article>' +
          '<article class="rs-card"><header class="rs-card__head"><div class="rs-card__icon">' +
          iconBell() +
          '</div><div><h2>Notification Preferences</h2><p>Manage how you receive important updates.</p></div></header>' +
          '<div class="rs-card__body"><div class="rs-notify-panel"><div class="rs-notify-panel__art">' +
          iconBell() +
          '</div><p>Notification preferences are not yet available. Important system notifications will appear in your FacultyLink portal when this feature is enabled.</p></div></div></article>' +
          '<article class="rs-card"><header class="rs-card__head"><div class="rs-card__icon">' +
          iconLock() +
          '</div><div><h2>Password &amp; Security</h2><p>Change your password to keep your account secure.</p></div></header>' +
          '<div class="rs-card__body"><form id="password-form" novalidate><div class="rs-password-grid">' +
          passwordField('current-password', 'current_password', 'Current Password', 'Current password', 'current-password') +
          passwordField('new-password', 'new_password', 'New Password', 'New password', 'new-password') +
          passwordField('confirm-password', 'confirm_password', 'Confirm New Password', 'Confirm password', 'new-password') +
          '</div><div class="rs-password-rules"><p>Password requirements</p><ul>' +
          '<li>At least 8 characters</li><li>At least one letter (A–Z or a–z)</li><li>At least one number (0–9)</li>' +
          '</ul></div><div class="rs-password-footer"><p class="ep-error" id="password-form-error" role="alert" hidden></p>' +
          '<button type="submit" class="fl-btn fl-btn--primary" id="password-submit"' +
          (state.passwordBusy ? ' disabled' : '') +
          '>' +
          (state.passwordBusy ? 'Updating…' : 'Change Password') +
          '</button></div></form></div></article></div>'

        bindPasswordToggles(el)
        var form = document.getElementById('password-form')
        if (form) form.addEventListener('submit', onPasswordSubmit)
      }

      function onPasswordSubmit(e) {
        e.preventDefault()
        state.error = ''
        state.notice = ''
        var form = e.target
        var submit = document.getElementById('password-submit')
        var current = form.current_password.value
        var next = form.new_password.value
        var confirm = form.confirm_password.value
        if (next !== confirm) {
          setPasswordError('New passwords do not match.')
          return
        }
        var policyErr = validatePasswordClient(next)
        if (policyErr) {
          setPasswordError(policyErr)
          return
        }
        setPasswordError('')
        state.passwordBusy = true
        if (submit) {
          submit.disabled = true
          submit.textContent = 'Updating…'
        }
        options
          .ensureCsrf()
          .then(function () {
            return options.changePassword(current, next)
          })
          .then(function (message) {
            state.notice = message + ' Please sign in again with your new password.'
            form.reset()
            return options.signOut()
          })
          .then(function () {
            global.location.href = loginPath
          })
          .catch(function (err) {
            state.passwordBusy = false
            setPasswordError(err.message || 'Unable to change password.')
            if (submit) {
              submit.disabled = false
              submit.textContent = 'Change Password'
            }
          })
      }

      function loadProfile() {
        state.loading = true
        state.error = ''
        paint()
        options
          .ensureCsrf()
          .then(function () {
            return options.fetchUser()
          })
          .then(function (user) {
            if (requiredRole && user.role !== requiredRole) {
              throw new Error(roleLabel + ' access required.')
            }
            state.user = user
            if (options.onUserLoaded) options.onUserLoaded(user)
            state.loading = false
            paint()
          })
          .catch(function (err) {
            state.loading = false
            state.error = err.message || 'Unable to load account settings.'
            paint()
          })
      }

      loadProfile()
    },
  }
})(window)
