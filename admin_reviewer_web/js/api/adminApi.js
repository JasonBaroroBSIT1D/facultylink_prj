/**
 * Admin API layer — future Flask REST integration.
 * All methods return Promises; swap implementations when backend is ready.
 */
(function (global) {
  function notConnected() {
    return Promise.reject(new Error('Backend not connected — using mock data only.'))
  }

  /** @type {import('../mock/adminMockData.js')} */
  var mock = global.FacultyLinkAdminMock

  var AdminApi = {
    /** Replace with: GET /api/admin/dashboard */
    getDashboardSummary: function () {
      return Promise.resolve(mock.dashboardSummary)
    },
    /** GET /api/v1/admin/users?role=faculty */
    listFaculty: function () {
      return global.FacultyLinkAdminHttp.adminFetch('/admin/users?role=faculty').then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to load faculty accounts.')
        return result.body.users
      })
    },
    /** GET /api/v1/admin/users?role=reviewer */
    listReviewers: function () {
      return global.FacultyLinkAdminHttp.adminFetch('/admin/users?role=reviewer').then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to load reviewer accounts.')
        return result.body.users
      })
    },
    createUser: function (payload) {
      return global.FacultyLinkAdminHttp.adminFetch('/admin/users', {
        method: 'POST',
        body: JSON.stringify(payload),
      }).then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to create account.')
        return result.body.user
      })
    },
    updateUser: function (userId, payload) {
      return global.FacultyLinkAdminHttp.adminFetch('/admin/users/' + userId, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }).then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to update account.')
        return result.body.user
      })
    },
    /** GET /api/admin/kra-config */
    getKraConfig: function () {
      var kras =
        global.FacultyLinkKraStructure && global.FacultyLinkKraStructure.buildAdminKras
          ? global.FacultyLinkKraStructure.buildAdminKras()
          : []
      return Promise.resolve({ _mock: true, kras: kras })
    },
    listEvaluationPeriods: function () {
      if (!global.FacultyLinkAdminHttp) {
        return global.FacultyLinkEvaluationPeriods.ready().then(function () {
          return global.FacultyLinkEvaluationPeriods.list()
        })
      }
      return global.FacultyLinkAdminHttp.adminFetch('/evaluation-periods').then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to load evaluation periods.')
        global.__facultylinkPeriodsFromServer = true
        global.FacultyLinkEvaluationPeriods.replaceAll(result.body.periods || [])
        return result.body.periods || []
      })
    },
    saveEvaluationPeriod: function (entry, id, acknowledgeOverlap) {
      if (!global.FacultyLinkAdminHttp) {
        return global.FacultyLinkEvaluationPeriods.ready().then(function () {
          if ((global.FacultyLinkMockAuth.loadSession() || {}).role !== 'admin') throw new Error('Administrator access required.')
          return global.FacultyLinkEvaluationPeriods.write(entry, id, acknowledgeOverlap)
        })
      }
      var payload = Object.assign({}, entry, { acknowledgeOverlap: !!acknowledgeOverlap })
      var path = id ? '/admin/evaluation-periods/' + encodeURIComponent(id) : '/admin/evaluation-periods'
      return global.FacultyLinkAdminHttp.adminFetch(path, {
        method: id ? 'PATCH' : 'POST',
        body: JSON.stringify(payload),
      }).then(function (result) {
        if (!result.ok) {
          if (result.status === 409 && result.body.overlaps) {
            var overlapError = new Error(result.body.message || 'Overlapping evaluation period.')
            overlapError.validation = { overlaps: result.body.overlaps }
            throw overlapError
          }
          if (result.body.fields) {
            var validationError = new Error(result.body.message || 'Check the evaluation period details.')
            validationError.validation = { errors: result.body.fields }
            throw validationError
          }
          throw new Error(result.body.message || 'Unable to save evaluation period.')
        }
        return global.FacultyLinkAdminApi.listEvaluationPeriods()
      })
    },
    closeEvaluationPeriod: function (id) {
      if (!global.FacultyLinkAdminHttp) {
        return global.FacultyLinkEvaluationPeriods.ready().then(function () {
          if ((global.FacultyLinkMockAuth.loadSession() || {}).role !== 'admin') throw new Error('Administrator access required.')
          return global.FacultyLinkEvaluationPeriods.close(id)
        })
      }
      return global.FacultyLinkAdminHttp.adminFetch('/admin/evaluation-periods/' + encodeURIComponent(id) + '/close-early', {
        method: 'POST',
        body: '{}',
      }).then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to close evaluation period.')
        return global.FacultyLinkAdminApi.listEvaluationPeriods()
      })
    },
    listReviewerAssignments: function (reviewerId) {
      return global.FacultyLinkAdminHttp.adminFetch('/admin/reviewers/' + reviewerId + '/assignments').then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to load assignments.')
        return result.body.assignments
      })
    },
    listAssignmentCandidates: function (reviewerId, query) {
      var q = query ? '?q=' + encodeURIComponent(query) : ''
      return global.FacultyLinkAdminHttp.adminFetch('/admin/reviewers/' + reviewerId + '/assignment-candidates' + q).then(
        function (result) {
          if (!result.ok) throw new Error(result.body.message || 'Unable to load faculty list.')
          return result.body.candidates
        }
      )
    },
    assignFacultyToReviewer: function (reviewerId, facultyIds) {
      return global.FacultyLinkAdminHttp.adminFetch('/admin/reviewers/' + reviewerId + '/assignments', {
        method: 'POST',
        body: JSON.stringify({ faculty_ids: facultyIds }),
      }).then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to assign faculty.')
        return result.body
      })
    },
    updateReviewerAssignment: function (assignmentId, payload) {
      return global.FacultyLinkAdminHttp.adminFetch('/admin/reviewer-assignments/' + assignmentId, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }).then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to update assignment.')
        return result.body.assignment
      })
    },
    /** GET /api/admin/scoring-rules */
    getScoringRules: function () {
      return Promise.resolve(mock.scoringRules)
    },
    /** GET /api/admin/documents */
    listDocumentMonitoring: function () {
      return Promise.resolve(mock.documentMonitoring)
    },
    /** GET /api/admin/rank-simulation */
    listRankSimulationMonitoring: function () {
      return Promise.resolve(mock.rankSimulation)
    },
    /** GET /api/admin/reports */
    getReports: function () {
      return Promise.resolve(mock.reports)
    },
    /** GET /api/admin/notifications */
    listNotifications: function () {
      return Promise.resolve(mock.notifications)
    },
    /** GET /api/admin/settings */
    getSettings: function () {
      return Promise.resolve(mock.settings)
    },
    /** Placeholder for future mutations */
    saveKraConfig: function () {
      return notConnected()
    },
    saveScoringRule: function () {
      return notConnected()
    },
  }

  global.FacultyLinkAdminApi = AdminApi
})(window)
