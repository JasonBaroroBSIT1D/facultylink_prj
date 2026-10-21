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
    /** GET /api/admin/faculty */
    listFaculty: function () {
      return Promise.resolve(mock.faculty)
    },
    /** GET /api/admin/reviewers */
    listReviewers: function () {
      return Promise.resolve(mock.reviewers)
    },
    /** GET /api/admin/kra-config */
    getKraConfig: function () {
      var kras =
        global.FacultyLinkKraStructure && global.FacultyLinkKraStructure.buildAdminKras
          ? global.FacultyLinkKraStructure.buildAdminKras()
          : []
      return Promise.resolve({ _mock: true, kras: kras })
    },
    /** GET /api/admin/evaluation-schedule */
    listEvaluationSchedule: function () {
      return Promise.resolve(
        global.FacultyLinkEvaluationSchedule
          ? global.FacultyLinkEvaluationSchedule.list()
          : []
      )
    },
    saveEvaluationSchedule: function (entry) {
      if (!global.FacultyLinkEvaluationSchedule) return notConnected()
      return Promise.resolve(global.FacultyLinkEvaluationSchedule.add(entry))
    },
    updateEvaluationSchedule: function (id, patch) {
      if (!global.FacultyLinkEvaluationSchedule) return notConnected()
      return Promise.resolve(global.FacultyLinkEvaluationSchedule.update(id, patch))
    },
    cancelEvaluationSchedule: function (id) {
      if (!global.FacultyLinkEvaluationSchedule) return notConnected()
      return Promise.resolve(global.FacultyLinkEvaluationSchedule.cancel(id))
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
