window.AdminPageInit = function (el, helpers) {
  var ui = window.FacultyLinkAdminAccountUi
  var state = { rows: [], filter: '', status: 'all', loading: true, error: '' }

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
        (profile.department && profile.department.toLowerCase().indexOf(q) >= 0)
      )
    })
  }

  function facultyCreateFormHtml() {
    var personal =
      ui.fieldHtml({
        id: 'fac-full-name',
        name: 'full_name',
        label: 'Full Name',
        required: true,
        placeholder: "Enter faculty member's full name",
        autocomplete: 'name',
      }) +
      ui.fieldHtml({
        id: 'fac-email',
        name: 'email',
        type: 'email',
        label: 'Email Address',
        required: true,
        placeholder: 'name@university.edu.ph',
        autocomplete: 'email',
      })
    var academic =
      ui.fieldHtml({
        id: 'fac-college',
        name: 'college',
        label: 'College',
        placeholder: 'Enter college',
        autocomplete: 'organization',
      }) +
      ui.fieldHtml({
        id: 'fac-department',
        name: 'department',
        label: 'Department',
        placeholder: 'Enter department',
        autocomplete: 'organization',
      }) +
      ui.fieldHtml({
        id: 'fac-rank',
        name: 'current_rank',
        label: 'Current Academic Rank',
        placeholder: 'Enter or select academic rank',
        wide: true,
      })
    var access =
      '<p class="admin-form-hint admin-form-field--wide">A welcome email with a temporary password will be sent automatically. The faculty member must change it on first sign-in in the mobile app.</p>'
    return (
      ui.sectionHtml('Personal Information', personal) +
      ui.sectionHtml('Academic Information', academic) +
      ui.sectionHtml('Account Access', access)
    )
  }

  function facultyEditFormHtml(user) {
    var p = user.faculty_profile || {}
    return (
      ui.sectionHtml(
        'Personal Information',
        ui.fieldHtml({
          id: 'fac-edit-name',
          name: 'full_name',
          label: 'Full Name',
          required: true,
          value: user.full_name,
          wide: true,
        }) +
          ui.fieldHtml({
            id: 'fac-edit-email',
            name: 'email',
            label: 'Email Address',
            value: user.email,
            disabled: true,
            wide: true,
          })
      ) +
      ui.sectionHtml(
        'Academic Information',
        ui.fieldHtml({
          id: 'fac-edit-college',
          name: 'college',
          label: 'College',
          value: p.college || '',
          placeholder: 'Enter college',
        }) +
          ui.fieldHtml({
            id: 'fac-edit-dept',
            name: 'department',
            label: 'Department',
            value: p.department || '',
            placeholder: 'Enter department',
          }) +
          ui.fieldHtml({
            id: 'fac-edit-rank',
            name: 'current_rank',
            label: 'Current Academic Rank',
            value: p.current_rank || '',
            placeholder: 'Enter or select academic rank',
            wide: true,
          })
      ) +
      ui.sectionHtml(
        'Account Access',
        '<div class="admin-form-field admin-form-field--wide" data-field="is_active"><label for="fac-edit-status">Account Status</label><select id="fac-edit-status" name="is_active" class="admin-field-input"><option value="true"' +
          (user.is_active ? ' selected' : '') +
          '>Active</option><option value="false"' +
          (!user.is_active ? ' selected' : '') +
          '>Inactive</option></select></div>'
      )
    )
  }

  function validateFacultyCreate(form) {
    return ui.validateClient(form, [
      { name: 'full_name', required: true, message: 'Enter the faculty member’s full name.' },
      { name: 'email', required: true, email: true, message: 'Enter a valid email address.' },
    ])
  }

  function resendInvite(user) {
    FacultyLinkAdminHttp.ensureCsrf()
      .then(function () {
        return FacultyLinkAdminApi.resendInvitation(user.user_id)
      })
      .then(function (result) {
        ui.toastForResendInvite(result, user.email)
        load()
      })
      .catch(function (err) {
        ui.showToast(ui.friendlyError(err), 'warning')
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
        state.rows = window.FacultyLinkAdminProductionAccounts.excludeDemoSeedAccounts(rows)
        state.loading = false
        state.error = ''
        paint()
      })
      .catch(function (err) {
        state.loading = false
        state.error = ui.friendlyError(err)
        paint()
      })
  }

  function openCreate() {
    ui.openFormModal({
      modalId: 'faculty-admin-modal',
      size: 'faculty',
      title: 'Add New Faculty',
      subtitle: "Enter the faculty member's details to create an account.",
      bodyHtml: facultyCreateFormHtml(),
      submitLabel: 'Create Faculty',
      submittingLabel: 'Creating account...',
      validate: validateFacultyCreate,
      onSubmit: function (fd) {
        return FacultyLinkAdminApi.createUser({
          role: 'faculty',
          full_name: fd.get('full_name'),
          email: fd.get('email'),
          college: fd.get('college'),
          department: fd.get('department'),
          current_rank: fd.get('current_rank'),
        })
      },
      onSuccess: function (result) {
        ui.toastForAccountCreate(result, 'Faculty account')
        load()
      },
    })
  }

  function openEdit(user) {
    ui.openFormModal({
      modalId: 'faculty-admin-modal',
      size: 'faculty',
      title: 'Edit Faculty Account',
      subtitle: 'Update account details and academic information.',
      bodyHtml: facultyEditFormHtml(user),
      submitLabel: 'Save Changes',
      submittingLabel: 'Saving...',
      validate: function (form) {
        return ui.validateClient(form, [{ name: 'full_name', required: true, message: 'Full name is required.' }])
      },
      onSubmit: function (fd) {
        var payload = {
          full_name: fd.get('full_name'),
          college: fd.get('college'),
          department: fd.get('department'),
          current_rank: fd.get('current_rank'),
          is_active: fd.get('is_active') === 'true',
        }
        return FacultyLinkAdminApi.updateUser(user.user_id, payload)
      },
      onSuccess: function () {
        load()
      },
    })
  }

  function paintTableBody(rows) {
    return rows
      .map(function (u) {
        var p = u.faculty_profile || {}
        return (
          '<tr><td>' +
          ui.personCell(u.full_name, u.email) +
          '</td><td>' +
          ui.esc(p.college || '—') +
          '</td><td>' +
          ui.esc(p.department || '—') +
          '</td><td>' +
          ui.esc(p.current_rank || '—') +
          '</td><td>' +
          helpers.statusBadge(u.is_active ? 'Active' : 'Inactive') +
          '</td><td>' +
          ui.esc(u.document_count != null ? u.document_count : 0) +
          '</td><td>' +
          ui.esc(u.kra_progress != null ? u.kra_progress : '—') +
          '</td><td><div class="admin-table__actions"><button type="button" class="fl-btn fl-btn--ghost" data-edit="' +
          u.user_id +
          '">Edit</button>' +
          (u.credentials_delivery_pending || u.must_set_password
            ? '<button type="button" class="fl-btn fl-btn--ghost" data-resend="' +
              u.user_id +
              '">Resend credentials</button>'
            : '') +
          '</div></td></tr>'
        )
      })
      .join('')
  }

  function paintPanelContent(filtered) {
    if (state.loading) {
      return ui.loadingState('Loading faculty accounts…')
    }
    if (state.error && !state.rows.length) {
      return ui.errorState(state.error, 'data-retry-load')
    }
    if (!state.rows.length) {
      return ui.emptyState({
        title: 'No faculty members yet',
        description: 'Add your first faculty member to get started.',
        actionLabel: 'Add Faculty',
      })
    }
    if (!filtered.length) {
      return ui.emptyState({
        title: 'No matching faculty members found.',
        description: '',
      })
    }
    return (
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr>' +
      '<th>Name</th><th>College</th><th>Department</th><th>Rank</th><th>Status</th><th>Documents</th><th>KRA Progress</th><th></th>' +
      '</tr></thead><tbody>' +
      paintTableBody(filtered) +
      '</tbody></table></div>'
    )
  }

  function paint() {
    var filtered = filteredRows()
    var countText = state.loading
      ? 'Loading…'
      : ui.countLabel(filtered.length, state.rows.length, 'faculty member', 'faculty members', state.filter, state.status)

    el.innerHTML =
      '<h1 class="admin-page-title">Faculty Management</h1>' +
      '<p class="admin-page-desc">Manage faculty accounts, update their information, and track their assessment progress in one place.</p>' +
      (state.error && state.rows.length
        ? '<p class="ep-notice" role="alert">' +
          ui.esc(state.error) +
          ' <button type="button" class="fl-btn fl-btn--ghost" style="margin-left:8px;padding:4px 10px;font-size:0.8rem" data-retry-load>Try again</button></p>'
        : '') +
      '<div class="admin-toolbar">' +
      '<button type="button" class="fl-btn fl-btn--primary" id="faculty-add">' +
      ui.iconUserPlus +
      'Add Faculty</button>' +
      '<input type="search" id="faculty-search" placeholder="Search faculty by name or email" value="' +
      ui.esc(state.filter) +
      '" aria-label="Search faculty" />' +
      '<select id="faculty-status" aria-label="Filter by status"><option value="all">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select>' +
      '</div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Faculty Members</h2><span class="fl-badge fl-badge--info">' +
      ui.esc(countText) +
      '</span></div>' +
      paintPanelContent(filtered) +
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
    el.querySelectorAll('[data-empty-action]').forEach(function (btn) {
      btn.addEventListener('click', openCreate)
    })
    el.querySelectorAll('[data-retry-load]').forEach(function (btn) {
      btn.addEventListener('click', load)
    })
    el.querySelectorAll('[data-edit]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var id = Number(btn.getAttribute('data-edit'))
        var user = state.rows.find(function (u) {
          return u.user_id === id
        })
        if (user) openEdit(user)
      })
    })
    el.querySelectorAll('[data-resend]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var id = Number(btn.getAttribute('data-resend'))
        var user = state.rows.find(function (u) {
          return u.user_id === id
        })
        if (user) resendInvite(user)
      })
    })
  }

  load()
}
