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
      if (state.status === 'inactive' && !u.is_active) return false
      if (!q) return true
      return (
        (u.full_name && u.full_name.toLowerCase().indexOf(q) >= 0) ||
        (u.email && u.email.toLowerCase().indexOf(q) >= 0)
      )
    })
  }

  function closeModal() {
    var node = document.getElementById('reviewer-admin-modal')
    if (node) node.remove()
  }

  function openModal(title, formHtml, onSubmit) {
    closeModal()
    var wrap = document.createElement('div')
    wrap.id = 'reviewer-admin-modal'
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
        return FacultyLinkAdminApi.listReviewers()
      })
      .then(function (rows) {
        state.rows = rows
        state.loading = false
        paint()
      })
      .catch(function (err) {
        state.loading = false
        state.error = err.message || 'Unable to load reviewer accounts.'
        paint()
      })
  }

  function openCreate() {
    openModal(
      'Add reviewer account',
      '<form class="admin-form-stack">' +
        '<label>Full name<input name="full_name" required /></label>' +
        '<label>Email<input name="email" type="email" required /></label>' +
        '<label>Initial password<input name="password" type="password" minlength="8" required /></label>' +
        '<p class="admin-form-error" data-error hidden></p>' +
        '<div class="admin-dialog__actions">' +
        '<button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
        '<button type="submit" class="fl-btn fl-btn--primary">Create account</button></div></form>',
      function (fd, errorEl) {
        errorEl.hidden = true
        FacultyLinkAdminApi.createUser({
          role: 'reviewer',
          full_name: fd.get('full_name'),
          email: fd.get('email'),
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

  function openAssign(reviewer) {
    var assignState = { assignments: [], candidates: [], filter: '', loading: true, error: '' }

    function openReassign(assignment, wrap) {
      var faculty = assignment.faculty || {}
      FacultyLinkAdminApi.listReviewers()
        .then(function (reviewers) {
          var options = reviewers
            .filter(function (r) {
              return r.is_active && r.user_id !== reviewer.user_id
            })
            .map(function (r) {
              return (
                '<option value="' +
                r.user_id +
                '">' +
                esc(r.full_name) +
                ' (' +
                esc(r.email) +
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
            '<div class="admin-dialog__panel" role="dialog" aria-modal="true">' +
            '<h2 class="admin-dialog__title">Reassign faculty</h2>' +
            '<p class="admin-page-desc">Move <strong>' +
            esc(faculty.full_name || 'faculty') +
            '</strong> from <strong>' +
            esc(reviewer.full_name) +
            '</strong> to another reviewer.</p>' +
            '<form class="admin-form-stack"><label>New reviewer<select name="reviewer_id" required>' +
            options +
            '</select></label>' +
            '<p class="admin-form-error" data-error hidden></p>' +
            '<div class="admin-dialog__actions">' +
            '<button type="button" class="fl-btn fl-btn--ghost" data-dismiss>Cancel</button>' +
            '<button type="submit" class="fl-btn fl-btn--primary">Confirm reassignment</button></div></form></div>'
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
                errorEl.textContent = err.message
                errorEl.hidden = false
              })
          })
        })
        .catch(function (err) {
          assignState.error = err.message
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
        (assignState.error ? '<p class="admin-form-error">' + esc(assignState.error) + '</p>' : '') +
        (assignState.loading
          ? '<p class="admin-page-desc">Loading assignments…</p>'
          : '<div class="admin-form-stack">' +
            '<label>Search faculty<input type="search" name="assign_filter" value="' +
            esc(assignState.filter) +
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
                      '<tr><td><strong>' +
                      esc(f.full_name) +
                      '</strong><br /><span style="font-size:0.78rem;color:var(--fl-text-muted)">' +
                      esc(f.email) +
                      '</span></td><td>' +
                      esc(f.department || '—') +
                      '</td><td><button type="button" class="fl-btn fl-btn--ghost" style="padding:4px 10px;font-size:0.78rem" data-reassign="' +
                      a.assignment_id +
                      '">Reassign</button> ' +
                      '<button type="button" class="fl-btn fl-btn--ghost" style="padding:4px 10px;font-size:0.78rem" data-unassign="' +
                      a.assignment_id +
                      '">Remove</button></td></tr>'
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
                      esc(c.full_name) +
                      ' · ' +
                      esc(c.department || '—') +
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
              assignState.error = err.message
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
        assignState.candidates = parts[1]
        assignState.loading = false
        renderAssignPanel(wrap)
      })
    }

    closeModal()
    var wrap = document.createElement('div')
    wrap.id = 'reviewer-admin-modal'
    wrap.className = 'admin-dialog'
    wrap.innerHTML =
      '<div class="admin-dialog__backdrop" data-dismiss></div>' +
      '<div class="admin-dialog__panel admin-dialog__panel--wide" role="dialog" aria-modal="true" style="max-width:720px">' +
      '<h2 class="admin-dialog__title">Assign faculty — ' +
      esc(reviewer.full_name) +
      '</h2>' +
      '<form class="admin-form-stack" data-assign-panel></form></div>'
    document.body.appendChild(wrap)
    wrap.addEventListener('click', function (e) {
      if (e.target.hasAttribute('data-dismiss')) closeModal()
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
            errorEl.textContent = err.message
            errorEl.hidden = false
          }
        })
    })
    reloadAssignments(wrap).catch(function (err) {
      assignState.loading = false
      assignState.error = err.message || 'Unable to load assignment data.'
      renderAssignPanel(wrap)
    })
  }

  function openEdit(user) {
    openModal(
      'Edit reviewer account',
      '<form class="admin-form-stack">' +
        '<label>Full name<input name="full_name" value="' +
        esc(user.full_name) +
        '" required /></label>' +
        '<label>Email<input value="' +
        esc(user.email) +
        '" disabled /></label>' +
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
      return '<p class="admin-page-desc">No reviewer accounts match the current filters.</p>'
    }
    return (
      '<div class="admin-table-wrap"><table class="admin-table"><thead><tr>' +
      '<th>ID</th><th>Name</th><th>Role</th><th>Assigned faculty</th><th>Queue</th><th>Status</th><th></th>' +
      '</tr></thead><tbody>' +
      rows
        .map(function (u) {
          return (
            '<tr><td>' +
            esc(u.user_id) +
            '</td><td><strong>' +
            esc(u.full_name) +
            '</strong><br /><span style="color:var(--fl-text-muted);font-size:0.78rem">' +
            esc(u.email) +
            '</span></td><td>Reviewer</td><td>' +
            esc(u.assigned_faculty_count != null ? u.assigned_faculty_count : 0) +
            '</td><td>' +
            esc(u.queue_count != null ? u.queue_count : 0) +
            '</td><td>' +
            statusBadge(u) +
            '</td><td><button type="button" class="fl-btn fl-btn--ghost" style="padding:6px 12px;font-size:0.8rem" data-edit="' +
            u.user_id +
            '">Edit</button> ' +
            '<button type="button" class="fl-btn fl-btn--ghost" style="padding:6px 12px;font-size:0.8rem" data-assign="' +
            u.user_id +
            '">Assign</button></td></tr>'
          )
        })
        .join('') +
      '</tbody></table></div>'
    )
  }

  function paint() {
    var rows = filteredRows()
    el.innerHTML =
      '<h1 class="admin-page-title">Reviewer Management</h1>' +
      '<p class="admin-page-desc">Assign reviewers, balance workloads, and configure verification permissions.</p>' +
      (state.error ? '<p class="ep-notice" role="alert">' + esc(state.error) + '</p>' : '') +
      '<div class="admin-toolbar">' +
      '<button type="button" class="fl-btn fl-btn--primary" id="reviewer-add">Invite Reviewer</button>' +
      '<input type="search" id="reviewer-search" placeholder="Search name or email…" value="' +
      esc(state.filter) +
      '" />' +
      '<select id="reviewer-status"><option value="all">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select>' +
      '</div>' +
      '<div class="admin-panel"><div class="admin-panel__head"><h2>Reviewers</h2><span class="fl-badge fl-badge--info">' +
      (state.loading ? 'Loading…' : rows.length + ' shown') +
      '</span></div>' +
      (state.loading ? '<p class="admin-page-desc">Loading reviewer accounts…</p>' : paintTable(rows)) +
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
  }

  load()
}
