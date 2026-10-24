window.AdminPageInit = function (el, helpers) {
  var ui = window.FacultyLinkAdminAccountUi
  var state = { rows: [], filter: '', status: 'all', loading: true, error: '' }

  function filteredRows() {
    var q = state.filter.trim().toLowerCase()
    return state.rows.filter(function (u) {
      if (state.status === 'active' && !u.is_active) return false
      if (state.status === 'inactive' && u.is_active) return false
      if (!q) return true
      return (
        (u.full_name && u.full_name.toLowerCase().indexOf(q) >= 0) ||
        (u.email && u.email.toLowerCase().indexOf(q) >= 0)
      )
    })
  }

  function closeAssignModal() {
    var node = document.getElementById('reviewer-admin-modal')
    if (node) node.remove()
  }

  function load() {
    state.loading = true
    state.error = ''
    paint()
    FacultyLinkAdminHttp.ensureCsrf()
      .then(function () {
        return FacultyLinkAdminApi.listReviewers()
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

  function reviewerCreateFormHtml() {
    var personal =
      ui.fieldHtml({
        id: 'rev-full-name',
        name: 'full_name',
        label: 'Full Name',
        required: true,
        placeholder: "Enter reviewer's full name",
        autocomplete: 'name',
        wide: true,
      }) +
      ui.fieldHtml({
        id: 'rev-email',
        name: 'email',
        type: 'email',
        label: 'Email Address',
        required: true,
        placeholder: 'name@university.edu.ph',
        autocomplete: 'email',
        wide: true,
      })
    var access =
      '<p class="admin-form-hint admin-form-field--wide">A welcome email with a temporary password will be sent automatically. The reviewer must change it on first sign-in.</p>'
    return ui.sectionHtml('Personal Information', personal) + ui.sectionHtml('Account Access', access)
  }

  function reviewerEditFormHtml(user) {
    return (
      ui.sectionHtml(
        'Personal Information',
        ui.fieldHtml({
          id: 'rev-edit-name',
          name: 'full_name',
          label: 'Full Name',
          required: true,
          value: user.full_name,
          wide: true,
        }) +
          ui.fieldHtml({
            id: 'rev-edit-email',
            name: 'email',
            label: 'Email Address',
            value: user.email,
            disabled: true,
            wide: true,
          })
      ) +
      ui.sectionHtml(
        'Account Access',
        '<div class="admin-form-field admin-form-field--wide" data-field="is_active"><label for="rev-edit-status">Account Status</label><select id="rev-edit-status" name="is_active" class="admin-field-input"><option value="true"' +
          (user.is_active ? ' selected' : '') +
          '>Active</option><option value="false"' +
          (!user.is_active ? ' selected' : '') +
          '>Inactive</option></select></div>'
      )
    )
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

  function openCreate() {
    ui.openFormModal({
      modalId: 'reviewer-admin-modal',
      size: 'reviewer',
      title: 'Add New Reviewer',
      subtitle: 'Create a reviewer account to help verify faculty submissions.',
      bodyHtml: reviewerCreateFormHtml(),
      submitLabel: 'Create Reviewer',
      submittingLabel: 'Creating account...',
      validate: function (form) {
        return ui.validateClient(form, [
          { name: 'full_name', required: true, message: 'Enter the reviewer’s full name.' },
          { name: 'email', required: true, email: true, message: 'Enter an email address.' },
        ])
      },
      onSubmit: function (fd) {
        return FacultyLinkAdminApi.createUser({
          role: 'reviewer',
          full_name: fd.get('full_name'),
          email: fd.get('email'),
        })
      },
      onSuccess: function (result) {
        ui.toastForAccountCreate(result, 'Reviewer account')
        load()
      },
    })
  }

  function openAssign(reviewer) {
    var assignState = { assignments: [], candidates: [], filter: '', loading: true, error: '' }

    function openReassign(assignment, wrap) {
      var faculty = assignment.faculty || {}
      FacultyLinkAdminApi.listReviewers()
        .then(function (reviewers) {
          var options = window.FacultyLinkAdminProductionAccounts.excludeDemoSeedAccounts(reviewers)
            .filter(function (r) {
              return r.is_active && r.user_id !== reviewer.user_id
            })
            .map(function (r) {
              return (
                '<option value="' +
                r.user_id +
                '">' +
                ui.esc(r.full_name) +
                ' (' +
                ui.esc(r.email) +
                ')</option>'
              )
            })
            .join('')
          if (!options) {
            assignState.error = 'No other active reviewers are available for reassignment.'
            renderAssignPanel(wrap)
            return
          }
          var node = document.createElement('div')
          node.className = 'admin-dialog'
          node.innerHTML =
            '<div class="admin-dialog__backdrop" data-dismiss></div>' +
            '<div class="admin-dialog__panel admin-dialog__panel--scroll" role="dialog" aria-modal="true">' +
            '<form class="admin-dialog__form"><header class="admin-dialog__header"><h2 class="admin-dialog__title">Reassign faculty</h2>' +
            '<p class="admin-dialog__subtitle">Move <strong>' +
            ui.esc(faculty.full_name || 'faculty') +
            '</strong> from <strong>' +
            ui.esc(reviewer.full_name) +
            '</strong> to another reviewer.</p></header>' +
            '<div class="admin-dialog__body"><div class="admin-form-field admin-form-field--wide" data-field="reviewer_id"><label for="reassign-reviewer">New reviewer</label>' +
            '<select id="reassign-reviewer" name="reviewer_id" class="admin-field-input" required>' +
            options +
            '</select></div>' +
            '<p class="admin-form-error" data-error hidden></p></div>' +
            '<footer class="admin-dialog__actions">' +
            '<button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
            '<button type="submit" class="fl-btn fl-btn--primary">Confirm reassignment</button></footer></form></div>'
          document.body.appendChild(node)
          node.addEventListener('click', function (e) {
            if (e.target.hasAttribute('data-dismiss')) node.remove()
          })
          node.querySelector('form').addEventListener('submit', function (e) {
            e.preventDefault()
            var errorEl = node.querySelector('[data-error]')
            errorEl.hidden = true
            var fd = new FormData(node.querySelector('form'))
            var newReviewerId = Number(fd.get('reviewer_id'))
            var newReviewer = reviewers.find(function (r) {
              return r.user_id === newReviewerId
            })
            if (
              !window.confirm(
                'Reassign ' +
                  (faculty.full_name || 'this faculty member') +
                  ' from ' +
                  reviewer.full_name +
                  ' to ' +
                  (newReviewer ? newReviewer.full_name : 'the selected reviewer') +
                  '?'
              )
            ) {
              return
            }
            FacultyLinkAdminApi.updateReviewerAssignment(assignment.assignment_id, { reviewer_id: newReviewerId })
              .then(function () {
                node.remove()
                return reloadAssignments(wrap)
              })
              .then(function () {
                load()
              })
              .catch(function (err) {
                errorEl.textContent = ui.friendlyError(err)
                errorEl.hidden = false
              })
          })
        })
        .catch(function (err) {
          assignState.error = ui.friendlyError(err)
          renderAssignPanel(wrap)
        })
    }

    function renderAssignPanel(wrap) {
      var panel = wrap.querySelector('[data-assign-panel]')
      if (!panel) return
      var assignedRows = assignState.assignments.filter(function (a) {
        var q = assignState.filter.trim().toLowerCase()
        if (!q) return true
        var f = a.faculty || {}
        return (
          (f.full_name && f.full_name.toLowerCase().indexOf(q) >= 0) ||
          (f.email && f.email.toLowerCase().indexOf(q) >= 0) ||
          (f.department && f.department.toLowerCase().indexOf(q) >= 0)
        )
      })
      var candidateRows = assignState.candidates.filter(function (c) {
        if (c.already_assigned) return false
        var q = assignState.filter.trim().toLowerCase()
        if (!q) return true
        return (
          (c.full_name && c.full_name.toLowerCase().indexOf(q) >= 0) ||
          (c.email && c.email.toLowerCase().indexOf(q) >= 0) ||
          (c.department && c.department.toLowerCase().indexOf(q) >= 0)
        )
      })

      panel.innerHTML =
        (assignState.error ? '<p class="admin-form-error">' + ui.esc(assignState.error) + '</p>' : '') +
        (assignState.loading
          ? ui.loadingState('Loading assignments…')
          : '<div class="admin-form-stack">' +
            '<label>Search faculty<input type="search" name="assign_filter" value="' +
            ui.esc(assignState.filter) +
            '" placeholder="Name, email, department…" /></label>' +
            '<h3 style="margin:16px 0 8px;font-size:0.95rem">Assigned faculty (' +
            assignState.assignments.length +
            ')</h3>' +
            (assignedRows.length
              ? '<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Name</th><th>Department</th><th></th></tr></thead><tbody>' +
                assignedRows
                  .map(function (a) {
                    var f = a.faculty || {}
                    return (
                      '<tr><td>' +
                      ui.personCell(f.full_name, f.email) +
                      '</td><td>' +
                      ui.esc(f.department || '—') +
                      '</td><td><div class="admin-table__actions"><button type="button" class="fl-btn fl-btn--ghost" data-reassign="' +
                      a.assignment_id +
                      '">Reassign</button>' +
                      '<button type="button" class="fl-btn fl-btn--ghost" data-unassign="' +
                      a.assignment_id +
                      '">Remove</button></div></td></tr>'
                    )
                  })
                  .join('') +
                '</tbody></table></div>'
              : '<p class="admin-page-desc">No faculty assigned yet.</p>') +
            '<h3 style="margin:16px 0 8px;font-size:0.95rem">Available faculty</h3>' +
            (candidateRows.length
              ? candidateRows
                  .map(function (c) {
                    return (
                      '<label style="display:flex;align-items:center;gap:8px;margin-bottom:8px;font-weight:500">' +
                      '<input type="checkbox" name="faculty_id" value="' +
                      c.faculty_id +
                      '" />' +
                      ui.esc(c.full_name) +
                      ' · ' +
                      ui.esc(c.department || '—') +
                      '</label>'
                    )
                  })
                  .join('')
              : '<p class="admin-page-desc">No additional active faculty match this filter.</p>') +
            '<p class="admin-form-error" data-error hidden></p>' +
            '<div class="admin-dialog__actions">' +
            '<button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Close</button>' +
            '<button type="submit" class="fl-btn fl-btn--primary">Assign selected</button></div></div>')

      var filterInput = panel.querySelector('[name="assign_filter"]')
      if (filterInput) {
        filterInput.addEventListener('input', function (e) {
          assignState.filter = e.target.value
          renderAssignPanel(wrap)
        })
      }
      panel.querySelectorAll('[data-reassign]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var assignmentId = Number(btn.getAttribute('data-reassign'))
          var row = assignState.assignments.find(function (a) {
            return a.assignment_id === assignmentId
          })
          if (row) openReassign(row, wrap)
        })
      })
      panel.querySelectorAll('[data-unassign]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var assignmentId = Number(btn.getAttribute('data-unassign'))
          btn.disabled = true
          FacultyLinkAdminApi.updateReviewerAssignment(assignmentId, { is_active: false })
            .then(function () {
              return reloadAssignments(wrap)
            })
            .then(function () {
              load()
            })
            .catch(function (err) {
              assignState.error = ui.friendlyError(err)
              renderAssignPanel(wrap)
            })
        })
      })
    }

    function reloadAssignments(wrap) {
      assignState.loading = true
      assignState.error = ''
      renderAssignPanel(wrap)
      return Promise.all([
        FacultyLinkAdminApi.listReviewerAssignments(reviewer.user_id),
        FacultyLinkAdminApi.listAssignmentCandidates(reviewer.user_id, assignState.filter),
      ]).then(function (parts) {
        assignState.assignments = parts[0]
        assignState.candidates = parts[1].filter(function (c) {
          return !window.FacultyLinkAdminProductionAccounts.isDemoSeedEmail(c.email)
        })
        assignState.loading = false
        renderAssignPanel(wrap)
      })
    }

    closeAssignModal()
    var wrap = document.createElement('div')
    wrap.id = 'reviewer-admin-modal'
    wrap.className = 'admin-dialog'
    wrap.innerHTML =
      '<div class="admin-dialog__backdrop" data-dismiss></div>' +
      '<div class="admin-dialog__panel admin-dialog__panel--wide admin-dialog__panel--scroll" role="dialog" aria-modal="true">' +
      '<header class="admin-dialog__header"><h2 class="admin-dialog__title">Assign faculty — ' +
      ui.esc(reviewer.full_name) +
      '</h2></header>' +
      '<form class="admin-dialog__form" data-assign-panel></form></div>'
    document.body.appendChild(wrap)
    wrap.addEventListener('click', function (e) {
      if (e.target.hasAttribute('data-dismiss')) closeAssignModal()
    })
    wrap.querySelector('form').addEventListener('submit', function (e) {
      e.preventDefault()
      var errorEl = wrap.querySelector('[data-error]')
      if (errorEl) errorEl.hidden = true
      var ids = Array.prototype.slice
        .call(wrap.querySelectorAll('input[name="faculty_id"]:checked'))
        .map(function (node) {
          return Number(node.value)
        })
      if (!ids.length) {
        if (errorEl) {
          errorEl.textContent = 'Select at least one faculty member.'
          errorEl.hidden = false
        }
        return
      }
      FacultyLinkAdminApi.assignFacultyToReviewer(reviewer.user_id, ids)
        .then(function () {
          return reloadAssignments(wrap)
        })
        .then(function () {
          load()
        })
        .catch(function (err) {
          if (errorEl) {
            errorEl.textContent = ui.friendlyError(err)
            errorEl.hidden = false
          }
        })
    })
    reloadAssignments(wrap).catch(function (err) {
      assignState.loading = false
      assignState.error = ui.friendlyError(err) || 'Unable to load assignment data.'
      renderAssignPanel(wrap)
    })
  }

  function openEdit(user) {
    ui.openFormModal({
      modalId: 'reviewer-admin-modal',
      size: 'reviewer',
      title: 'Edit Reviewer Account',
      subtitle: 'Update reviewer account details and access.',
      bodyHtml: reviewerEditFormHtml(user),
      submitLabel: 'Save Changes',
      submittingLabel: 'Saving...',
      validate: function (form) {
        return ui.validateClient(form, [{ name: 'full_name', required: true, message: 'Full name is required.' }])
      },
      onSubmit: function (fd) {
        var payload = {
          full_name: fd.get('full_name'),
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
        return (
          '<tr><td>' +
          ui.personCell(u.full_name, u.email) +
          '</td><td>' +
          ui.esc(u.assigned_faculty_count != null ? u.assigned_faculty_count : 0) +
          '</td><td>' +
          ui.esc(u.queue_count != null ? u.queue_count : 0) +
          '</td><td>' +
          helpers.statusBadge(u.is_active ? 'Active' : 'Inactive') +
          '</td><td><div class="admin-table__actions"><button type="button" class="fl-btn fl-btn--ghost" data-edit="' +
          u.user_id +
          '">Edit</button>' +
          (u.credentials_delivery_pending || u.must_set_password
            ? '<button type="button" class="fl-btn fl-btn--ghost" data-resend="' +
              u.user_id +
              '">Resend credentials</button>'
            : '') +
          '<button type="button" class="fl-btn fl-btn--ghost" data-assign="' +
          u.user_id +
          '">Assign</button></div></td></tr>'
        )
      })
      .join('')
  }

  function paintPanelContent(filtered) {
    if (state.loading) {
      return ui.loadingState('Loading reviewer accounts…')
    }
    if (state.error && !state.rows.length) {
      return ui.errorState(state.error, 'data-retry-load')
    }
    if (!state.rows.length) {
      return ui.emptyState({
        title: 'No reviewers yet',
        description: 'Create a reviewer account to start assigning faculty members.',
        actionLabel: 'Add Reviewer',
      })
    }
    if (!filtered.length) {
      return ui.emptyState({
        title: 'No matching reviewers found.',
        description: '',
      })
    }
    return (
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr>' +
      '<th>Name</th><th>Assigned Faculty</th><th>Pending Reviews</th><th>Status</th><th></th>' +
      '</tr></thead><tbody>' +
      paintTableBody(filtered) +
      '</tbody></table></div>'
    )
  }

  function paint() {
    var filtered = filteredRows()
    var countText = state.loading
      ? 'Loading…'
      : ui.countLabel(filtered.length, state.rows.length, 'reviewer', 'reviewers', state.filter, state.status)

    el.innerHTML =
      '<h1 class="admin-page-title">Reviewer Management</h1>' +
      '<p class="admin-page-desc">Manage reviewer accounts, assign faculty members, and keep track of pending reviews.</p>' +
      (state.error && state.rows.length
        ? '<p class="ep-notice" role="alert">' +
          ui.esc(state.error) +
          ' <button type="button" class="fl-btn fl-btn--ghost" style="margin-left:8px;padding:4px 10px;font-size:0.8rem" data-retry-load>Try again</button></p>'
        : '') +
      '<div class="admin-toolbar">' +
      '<button type="button" class="fl-btn fl-btn--primary" id="reviewer-add">' +
      ui.iconUserPlus +
      'Add Reviewer</button>' +
      '<input type="search" id="reviewer-search" placeholder="Search reviewers by name or email" value="' +
      ui.esc(state.filter) +
      '" aria-label="Search reviewer" />' +
      '<select id="reviewer-status" aria-label="Filter by status"><option value="all">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select>' +
      '</div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Reviewer Accounts</h2><span class="fl-badge fl-badge--info">' +
      ui.esc(countText) +
      '</span></div>' +
      paintPanelContent(filtered) +
      '</div>'

    var statusSelect = document.getElementById('reviewer-status')
    if (statusSelect) statusSelect.value = state.status
    var search = document.getElementById('reviewer-search')
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
    document.getElementById('reviewer-add').addEventListener('click', openCreate)
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
    el.querySelectorAll('[data-assign]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var id = Number(btn.getAttribute('data-assign'))
        var user = state.rows.find(function (u) {
          return u.user_id === id
        })
        if (user) openAssign(user)
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
