window.FacultyLinkAdminAccountUi = (function () {
  var lastFocus = null

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    })
  }

  function initials(name) {
    return (name || '?')
      .trim()
      .split(/\s+/)
      .map(function (p) {
        return p[0]
      })
      .slice(0, 2)
      .join('')
      .toUpperCase()
  }

  function personCell(name, email) {
    return (
      '<div class="admin-person-cell">' +
      '<div class="admin-avatar" aria-hidden="true">' +
      esc(initials(name)) +
      '</div><div class="admin-person-cell__text"><span class="admin-person-cell__name">' +
      esc(name) +
      '</span><span class="admin-person-cell__email">' +
      esc(email) +
      '</span></div></div>'
    )
  }

  function hasActiveFilters(filter, status) {
    return Boolean(filter && filter.trim()) || (status && status !== 'all')
  }

  function countLabel(filtered, total, singular, plural, filter, status) {
    var word = filtered === 1 ? singular : plural
    if (hasActiveFilters(filter, status) && filtered !== total) {
      return filtered + ' of ' + total + ' ' + (total === 1 ? singular : plural)
    }
    return filtered + ' ' + word
  }

  function toastForAccountCreate(result, label) {
    var ed = result && result.email_delivery
    if (ed && ed.sent === false) {
      showToast(
        label +
          ' was saved, but credential email delivery failed. Use Resend credentials after fixing SMTP. ' +
          (ed.message || ''),
        'warning'
      )
      return
    }
    if (ed && ed.sent) {
      showToast(label + ' created. Credential email sent.')
      return
    }
    showToast(label + ' created successfully.')
  }

  function toastForResendInvite(result, email) {
    var ed = result && result.email_delivery
    if (ed && ed.sent) {
      showToast('Credential email sent to ' + email + '.')
    } else {
      showToast(
        'Could not send credential email. ' + ((ed && ed.message) || 'Check SMTP settings.'),
        'warning'
      )
    }
  }

  function showToast(message, tone) {
    var node = document.createElement('div')
    node.className = 'admin-flash admin-flash--' + (tone || 'success')
    node.setAttribute('role', 'status')
    node.textContent = message
    document.body.appendChild(node)
    window.setTimeout(function () {
      if (node.parentNode) node.remove()
    }, 4500)
  }

  function friendlyError(err) {
    var msg = err && err.message ? String(err.message) : 'Something went wrong. Please try again.'
    if (/failed to fetch|network/i.test(msg)) {
      return 'Unable to reach the server. Check your connection and try again.'
    }
    return msg
  }

  function fieldHtml(opts) {
    var id = opts.id
    var required = opts.required ? ' <span class="admin-field-required">*</span>' : ''
    var invalid = opts.invalid ? ' is-invalid' : ''
    var err = opts.error ? '<p class="admin-field-error" id="' + esc(id) + '-error">' + esc(opts.error) + '</p>' : ''
    var inputAttrs =
      ' id="' +
      esc(id) +
      '" name="' +
      esc(opts.name) +
      '" class="admin-field-input' +
      invalid +
      '"'
    if (opts.type) inputAttrs += ' type="' + esc(opts.type) + '"'
    if (opts.required) inputAttrs += ' required'
    if (opts.minlength) inputAttrs += ' minlength="' + opts.minlength + '"'
    if (opts.placeholder) inputAttrs += ' placeholder="' + esc(opts.placeholder) + '"'
    if (opts.autocomplete) inputAttrs += ' autocomplete="' + esc(opts.autocomplete) + '"'
    if (opts.value != null) inputAttrs += ' value="' + esc(opts.value) + '"'
    if (opts.disabled) inputAttrs += ' disabled'

    var input
    if (opts.passwordToggle) {
      input =
        '<div class="admin-password-field">' +
        '<input' +
        inputAttrs +
        ' />' +
        '<button type="button" class="admin-password-field__toggle" data-toggle-password aria-label="Show password" aria-pressed="false">' +
        '<span aria-hidden="true">Show</span></button></div>'
    } else {
      input = '<input' + inputAttrs + ' />'
    }

    var helper = opts.helper
      ? '<p class="admin-field-helper" id="' + esc(id) + '-helper">' + esc(opts.helper) + '</p>'
      : ''

    return (
      '<div class="admin-form-field' +
      (opts.wide ? ' admin-form-field--wide' : '') +
      '" data-field="' +
      esc(opts.name) +
      '">' +
      '<label for="' +
      esc(id) +
      '">' +
      esc(opts.label) +
      required +
      '</label>' +
      input +
      helper +
      err +
      '</div>'
    )
  }

  var modalHeaderIcon =
    '<span class="admin-modal-icon" aria-hidden="true">' +
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="10" cy="8" r="3.5" stroke="currentColor" stroke-width="1.6"/><path d="M4 20c0-3.3 2.7-6 6-6" stroke="currentColor" stroke-width="1.6"/><path d="M19 8v6M16 11h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>' +
    '</span>'

  function sectionHtml(title, inner) {
    return '<fieldset class="admin-form-section"><legend>' + esc(title) + '</legend><div class="admin-form-section__grid">' + inner + '</div></fieldset>'
  }

  function bindPasswordToggles(root) {
    root.querySelectorAll('[data-toggle-password]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var wrap = btn.closest('.admin-password-field')
        var input = wrap && wrap.querySelector('input')
        if (!input) return
        var show = input.type === 'password'
        input.type = show ? 'text' : 'password'
        btn.setAttribute('aria-pressed', show ? 'true' : 'false')
        btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password')
        var label = btn.querySelector('span')
        if (label) label.textContent = show ? 'Hide' : 'Show'
      })
    })
  }

  function clearFieldErrors(form) {
    form.querySelectorAll('.is-invalid').forEach(function (el) {
      el.classList.remove('is-invalid')
    })
    form.querySelectorAll('.admin-field-error').forEach(function (el) {
      el.remove()
    })
    var global = form.querySelector('[data-error]')
    if (global) {
      global.hidden = true
      global.textContent = ''
    }
  }

  function setFieldError(form, name, message) {
    var field = form.querySelector('[data-field="' + name + '"]')
    if (!field) return
    var input = field.querySelector('input, select, textarea')
    if (input) input.classList.add('is-invalid')
    var err = document.createElement('p')
    err.className = 'admin-field-error'
    err.id = (input && input.id ? input.id : name) + '-error'
    err.textContent = message
    field.appendChild(err)
  }

  function validateClient(form, rules) {
    clearFieldErrors(form)
    var fd = new FormData(form)
    var ok = true
    rules.forEach(function (rule) {
      var val = (fd.get(rule.name) || '').toString().trim()
      if (rule.required && !val) {
        setFieldError(form, rule.name, rule.message || 'This field is required.')
        ok = false
        return
      }
      if (rule.minlength && val && val.length < rule.minlength) {
        setFieldError(form, rule.name, rule.minlengthMessage || 'Please enter at least ' + rule.minlength + ' characters.')
        ok = false
      }
      if (rule.email && val && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
        setFieldError(form, rule.name, 'Enter a valid email address.')
        ok = false
      }
    })
    return ok
  }

  function openFormModal(options) {
    var ui = window.FacultyLinkAdminAccountUi
    var modalId = options.modalId || 'admin-account-modal'
    var existing = document.getElementById(modalId)
    if (existing) existing.remove()

    lastFocus = document.activeElement

    var wrap = document.createElement('div')
    wrap.id = modalId
    wrap.className = 'admin-dialog'
    var sizeClass = options.size === 'reviewer' ? ' admin-dialog__panel--reviewer' : ' admin-dialog__panel--faculty'

    wrap.innerHTML =
      '<div class="admin-dialog__backdrop" data-dismiss tabindex="-1"></div>' +
      '<div class="admin-dialog__panel admin-dialog__panel--scroll' +
      sizeClass +
      '" role="dialog" aria-modal="true" aria-labelledby="' +
      esc(modalId) +
      '-title">' +
      '<form class="admin-dialog__form" novalidate>' +
      '<header class="admin-dialog__header">' +
      '<div class="admin-dialog__header-row">' +
      (options.showHeaderIcon !== false ? modalHeaderIcon : '') +
      '<div class="admin-dialog__header-text">' +
      '<h2 class="admin-dialog__title" id="' +
      esc(modalId) +
      '-title">' +
      esc(options.title) +
      '</h2>' +
      (options.subtitle ? '<p class="admin-dialog__subtitle">' + esc(options.subtitle) + '</p>' : '') +
      '</div>' +
      '<button type="button" class="admin-dialog__close" data-dismiss aria-label="Close dialog">&times;</button>' +
      '</div></header>' +
      '<div class="admin-dialog__body">' +
      options.bodyHtml +
      '<p class="admin-form-error" data-error hidden role="alert"></p>' +
      '</div>' +
      '<footer class="admin-dialog__actions">' +
      '<button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
      '<button type="submit" class="fl-btn fl-btn--primary" data-submit>' +
      esc(options.submitLabel || 'Save') +
      '</button></footer></form></div>'

    document.body.appendChild(wrap)

    function close() {
      wrap.remove()
      document.removeEventListener('keydown', onKey)
      if (lastFocus && typeof lastFocus.focus === 'function') {
        try {
          lastFocus.focus()
        } catch (e) {}
      }
    }

    function onKey(e) {
      if (e.key === 'Escape') {
        e.preventDefault()
        close()
      }
    }

    document.addEventListener('keydown', onKey)
    wrap.addEventListener('click', function (e) {
      if (e.target.hasAttribute('data-dismiss')) close()
    })

    bindPasswordToggles(wrap)

    var form = wrap.querySelector('form')
    var submitBtn = wrap.querySelector('[data-submit]')
    var errorEl = wrap.querySelector('[data-error]')

    form.addEventListener('submit', function (e) {
      e.preventDefault()
      if (options.validate && !options.validate(form)) return
      errorEl.hidden = true
      submitBtn.disabled = true
      var prevLabel = submitBtn.textContent
      submitBtn.textContent = options.submittingLabel || 'Saving…'
      Promise.resolve(
        options.onSubmit(new FormData(form), errorEl, {
          enable: function () {
            submitBtn.disabled = false
            submitBtn.textContent = prevLabel
          },
        })
      )
        .then(function (result) {
          if (result && result.keepOpen) {
            submitBtn.disabled = false
            submitBtn.textContent = prevLabel
            return
          }
          close()
          if (options.onSuccess) options.onSuccess(result)
        })
        .catch(function (err) {
          errorEl.textContent = friendlyError(err)
          errorEl.hidden = false
          submitBtn.disabled = false
          submitBtn.textContent = prevLabel
        })
    })

    var first = form.querySelector('input:not([disabled]), select, textarea')
    if (first) window.setTimeout(function () { first.focus() }, 0)

    return { close: close, root: wrap }
  }

  var iconUserPlus =
    '<svg class="admin-btn-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'

  function emptyState(opts) {
    return (
      '<div class="admin-empty-state">' +
      '<p class="admin-empty-state__title">' +
      esc(opts.title) +
      '</p>' +
      (opts.description
        ? '<p class="admin-empty-state__desc">' + esc(opts.description) + '</p>'
        : '') +
      (opts.actionLabel
        ? '<button type="button" class="fl-btn fl-btn--primary" data-empty-action>' + esc(opts.actionLabel) + '</button>'
        : '') +
      '</div>'
    )
  }

  function loadingState(message) {
    return (
      '<div class="admin-loading-state" role="status">' +
      '<span class="admin-loading-state__spinner" aria-hidden="true"></span>' +
      '<p>' +
      esc(message || 'Loading accounts…') +
      '</p></div>'
    )
  }

  function errorState(message, retryAttr) {
    return (
      '<div class="admin-error-state" role="alert">' +
      '<p>' +
      esc(message) +
      '</p>' +
      '<button type="button" class="fl-btn fl-btn--primary" ' +
      retryAttr +
      '>Try again</button></div>'
    )
  }

  return {
    esc: esc,
    personCell: personCell,
    countLabel: countLabel,
    hasActiveFilters: hasActiveFilters,
    showToast: showToast,
    toastForAccountCreate: toastForAccountCreate,
    toastForResendInvite: toastForResendInvite,
    fieldHtml: fieldHtml,
    sectionHtml: sectionHtml,
    openFormModal: openFormModal,
    validateClient: validateClient,
    iconUserPlus: iconUserPlus,
    modalHeaderIcon: modalHeaderIcon,
    emptyState: emptyState,
    loadingState: loadingState,
    errorState: errorState,
    friendlyError: friendlyError,
  }
})()
