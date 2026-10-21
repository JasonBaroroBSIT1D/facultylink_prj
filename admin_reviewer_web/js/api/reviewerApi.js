/**
 * Reviewer API — future Flask REST integration.
 */
(function (global) {
  var mock = global.FacultyLinkReviewerMock

  function notConnected() {
    return Promise.reject(new Error('Backend not connected'))
  }

  global.FacultyLinkReviewerApi = {
    getDashboard: function () {
      return Promise.resolve(mock.dashboard)
    },
    listAssignedFaculty: function () {
      return Promise.resolve(mock.assignedFaculty)
    },
    getFacultyOverview: function (id) {
      if (mock.facultyOverview[id]) return Promise.resolve(mock.facultyOverview[id])
      var f = mock.assignedFaculty.find(function (x) {
        return x.id === id
      })
      if (!f) return Promise.resolve(null)
      return Promise.resolve({
        name: f.name,
        kraSummary: [
          { kra: 'KRA I', progress: 'Assessment in progress (mock)', docs: f.documents },
          { kra: 'KRA II', progress: 'Pending backend config', docs: '—' },
          { kra: 'KRA III', progress: 'Pending backend config', docs: '—' },
          { kra: 'KRA IV', progress: 'Pending backend config', docs: '—' },
        ],
      })
    },
    listDocuments: function () {
      return Promise.resolve(mock.documents)
    },
    getDocument: function (id) {
      var doc = mock.documents.find(function (d) {
        return d.id === id
      })
      return Promise.resolve(doc || null)
    },
    getKraAssessment: function (facultyId) {
      var kras =
        global.FacultyLinkKraStructure && global.FacultyLinkKraStructure.buildReviewerKras
          ? global.FacultyLinkKraStructure.buildReviewerKras()
          : []
      return Promise.resolve({
        facultyId: facultyId || mock.kraAssessment.facultyId,
        facultyName: mock.kraAssessment.facultyName,
        kras: kras,
      })
    },
    listEvaluationSchedule: function () {
      var session = global.FacultyLinkMockAuth && global.FacultyLinkMockAuth.loadSession()
      var reviewerId = session && session.reviewerId ? session.reviewerId : 'R-01'
      return Promise.resolve(
        global.FacultyLinkEvaluationSchedule
          ? global.FacultyLinkEvaluationSchedule.listForReviewer(reviewerId)
          : []
      )
    },
    listRankSimulations: function () {
      return Promise.resolve(mock.rankSimulation)
    },
    getEvaluationHistory: function () {
      return Promise.resolve(mock.evaluationHistory)
    },
    listNotifications: function () {
      return Promise.resolve(mock.notifications)
    },
    getSettings: function () {
      return Promise.resolve(mock.settings)
    },
    submitReviewDecision: function () {
      return notConnected()
    },
  }
})(window)
