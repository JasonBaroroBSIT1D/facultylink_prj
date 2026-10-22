window.AdminPageInit = function (el, helpers) {
  var state = { rows: [], filter: '', status: 'all', loading: true, error: '' }

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    })
  }

  function statusBadge(user) {
    return helpers.statusBadge(user.is_active ? 'Active' : 'Inactive')
  }

  function filteredRows() {
    var q = state.filter.trim().toLowerCase()
    return state.rows.filter(function (u) {
      if (state.status === 'active' && !u.is_active) return false
      if (state.status === 'inactive' && u.is_active) return false
      if (!q) return true
      var profile = u.faculty_profile || {}
      return (
        (u.full_name && u.full_name.toLowerCase().indexOf(q) >= 0) ||
        (u.email && u.email.toLowerCase().indexOf(q) >= 0) ||
        (profile.department && profile.department.toLowerCase().indexOf(q) >= 0) ||
        (profile.employee_number && profile.employee_number.toLowerCase().indexOf(q) >= 0)
      )
    })
  }

  function closeModal() {
    var node = document.getElementById('faculty-admin-modal')
    if (node) node.remove()
  }

  function openModal(title, formHtml, onSubmit) {
    closeModal()
    var wrap = document.createElement('div')
    wrap.id = 'faculty-admin-modal'
    wrap.className = 'admin-dialog'
    wrap.innerHTML =
      '<div class="admin-dialog__backdrop" data-dismiss></div>' +
      '<div class="admin-dialog__panel" role="dialog" aria-modal="true">' +
      '<h2 class="admin-dialog__title">' +
      esc(title) +
      '</h2>' +
      formHtml +
      '</div>'
    document.body.appendChild(wrap)
    wrap.addEventListener('click', function (e) {
      if (e.target.hasAttribute('data-dismiss')) closeModal()
    })
    var form = wrap.querySelector('form')
    form.addEventListener('submit', function (e) {
      e.preventDefault()
      onSubmit(new FormData(form), wrap.querySelector('[data-error]'))
    })
  }

  function load() {
    state.loading = true
    state.error = ''
    paint()
    FacultyLinkAdminHttp.ensureCsrf()
      .then(function () {
        return FacultyLinkAdminApi.listFaculty()
      })
      .then(function (rows) {
        state.rows = rows
        state.loading = false
        paint()
      })
      .catch(function (err) {
        state.loading = false
        state.error = err.message || 'Unable to load faculty roster.'
        paint()
      })
  }

  function openCreate() {
    openModal(
      'Add faculty account',
      '<form class="admin-form-stack">' +
        '<label>Full name<input name="full_name" required /></label>' +
        '<label>Email<input name="email" type="email" required /></label>' +
        '<label>Employee number<input name="employee_number" required /></label>' +
        '<label>College<input name="college" /></label>' +
        '<label>Department<input name="department" required /></label>' +
        '<label>Current rank<input name="current_rank" /></label>' +
        '<label>Initial password<input name="password" type="password" minlength="8" required /></label>' +
        '<p class="admin-form-error" data-error hidden></p>' +
        '<div class="admin-dialog__actions">' +
        '<button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
        '<button type="submit" class="fl-btn fl-btn--primary">Create account</button></div></form>',
      function (fd, errorEl) {
        errorEl.hidden = true
        FacultyLinkAdminApi.createUser({
          role: 'faculty',
          full_name: fd.get('full_name'),
          email: fd.get('email'),
          employee_number: fd.get('employee_number'),
          college: fd.get('college'),
          department: fd.get('department'),
          current_rank: fd.get('current_rank'),
          password: fd.get('password'),
        })
          .then(function () {
            closeModal()
            load()
          })
          .catch(function (err) {
            errorEl.textContent = err.message
            errorEl.hidden = false
          })
      }
    )
  }

  function openEdit(user) {
    var p = user.faculty_profile || {}
    openModal(
      'Edit faculty account',
      '<form class="admin-form-stack">' +
        '<label>Full name<input name="full_name" value="' +
        esc(user.full_name) +
        '" required /></label>' +
        '<label>Email<input value="' +
        esc(user.email) +
        '" disabled /></label>' +
        '<label>Employee number<input name="employee_number" value="' +
        esc(p.employee_number || '') +
        '" required /></label>' +
        '<label>College<input name="college" value="' +
        esc(p.college || '') +
        '" /></label>' +
        '<label>Department<input name="department" value="' +
        esc(p.department || '') +
        '" required /></label>' +
        '<label>Current rank<input name="current_rank" value="' +
        esc(p.current_rank || '') +
        '" /></label>' +
        '<label>Account status<select name="is_active">' +
        '<option value="true"' +
        (user.is_active ? ' selected' : '') +
        '>Active</option><option value="false"' +
        (!user.is_active ? ' selected' : '') +
        '>Inactive</option></select></label>' +
        '<label>New password (optional)<input name="password" type="password" minlength="8" placeholder="Leave blank to keep current" /></label>' +
        '<p class="admin-form-error" data-error hidden></p>' +
        '<div class="admin-dialog__actions">' +
        '<button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
        '<button type="submit" class="fl-btn fl-btn--primary">Save changes</button></div></form>',
      function (fd, errorEl) {
        errorEl.hidden = true
        var payload = {
          full_name: fd.get('full_name'),
          employee_number: fd.get('employee_number'),
          college: fd.get('college'),
          department: fd.get('department'),
          current_rank: fd.get('current_rank'),
          is_active: fd.get('is_active') === 'true',
        }
        if (fd.get('password')) payload.password = fd.get('password')
        FacultyLinkAdminApi.updateUser(user.user_id, payload)
          .then(function () {
            closeModal()
            load()
          })
          .catch(function (err) {
            errorEl.textContent = err.message
            errorEl.hidden = false
          })
      }
    )
  }

  function paintTable(rows) {
    if (!rows.length) {
      return '<p class="admin-page-desc">No faculty accounts match the current filters.</p>'
    }
    return (
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr>' +
      '<th>ID</th><th>Name</th><th>Department</th><th>Rank</th><th>Status</th><th>Docs</th><th>KRA progress</th><th></th>' +
      '</tr></thead><tbody>' +
      rows
        .map(function (u) {
          var p = u.faculty_profile || {}
          return (
            '<tr><td>' +
            esc(p.employee_number || u.user_id) +
            '</td><td><strong>' +
            esc(u.full_name) +
            '</strong><br /><span style="color:var(--fl-text-muted);font-size:0.78rem">' +
            esc(u.email) +
            '</span></td><td>' +
            esc(p.department || '—') +
            '</td><td>' +
            esc(p.current_rank || '—') +
            '</td><td>' +
            statusBadge(u) +
            '</td><td>' +
            esc(u.document_count != null ? u.document_count : 0) +
            '</td><td>' +
            esc(u.kra_progress != null ? u.kra_progress : '—') +
            '</td><td><button type="button" class="fl-btn fl-btn--ghost" style="padding:6px 12px;font-size:0.8rem" data-edit="' +
            u.user_id +
            '">Edit</button></td></tr>'
          )
        })
        .join('') +
      '</tbody></table></div>'
    )
  }

  function paint() {
    var rows = filteredRows()
    el.innerHTML =
      '<h1 class="admin-page-title">Faculty Management</h1>' +
      '<p class="admin-page-desc">Register, monitor, and manage faculty accounts linked to self-assessment workflows.</p>' +
      (state.error ? '<p class="ep-notice" role="alert">' + esc(state.error) + '</p>' : '') +
      '<div class="admin-toolbar">' +
      '<button type="button" class="fl-btn fl-btn--primary" id="faculty-add">Add Faculty</button>' +
      '<button type="button" class="fl-btn fl-btn--ghost" disabled title="CSV import is not available yet">Import CSV</button>' +
      '<input type="search" id="faculty-search" placeholder="Search name, email, department…" value="' +
      esc(state.filter) +
      '" />' +
      '<select id="faculty-status"><option value="all">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select>' +
      '</div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Faculty roster</h2><span class="fl-badge fl-badge--info">' +
      (state.loading ? 'Loading…' : rows.length + ' shown') +
      '</span></div>' +
      (state.loading ? '<p class="admin-page-desc">Loading faculty accounts…</p>' : paintTable(rows)) +
      '</div>'

    var statusSelect = document.getElementById('faculty-status')
    if (statusSelect) statusSelect.value = state.status
    var search = document.getElementById('faculty-search')
    if (search) {
      search.addEventListener('input', function (e) {
        state.filter = e.target.value
        paint()
      })
    }
    if (statusSelect) {
      statusSelect.addEventListener('change', function (e) {
        state.status = e.target.value
        paint()
      })
    }
    var addBtn = document.getElementById('faculty-add')
    if (addBtn) addBtn.addEventListener('click', openCreate)
    el.querySelectorAll('[data-edit]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var id = Number(btn.getAttribute('data-edit'))
        var user = state.rows.find(function (u) {
          return u.user_id === id
        })
        if (user) openEdit(user)
      })
    })
  }

  el.addEventListener('click', function () {})
  load()
}
