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
    listAssignedFaculty: function (query) {
      var q = query ? '?q=' + encodeURIComponent(query) : ''
      return global.FacultyLinkReviewerHttp.reviewerFetch('/reviewer/assigned-faculty' + q).then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to load assigned faculty.')
        return result.body.faculty
      })
    },
    getFacultyOverview: function (id) {
      return global.FacultyLinkReviewerHttp.reviewerFetch('/reviewer/assigned-faculty/' + encodeURIComponent(id)).then(
        function (result) {
          if (!result.ok) return null
          var f = result.body.faculty
          return {
            name: f.name,
            kraSummary: ['KRA I', 'KRA II', 'KRA III', 'KRA IV'].map(function (kra) {
              var docs = mock.documents.filter(function (d) {
                return String(d.facultyId) === String(id) && d.kra === kra
              })
              return {
                kra: kra,
                progress: docs.length ? 'Sample documents available for review' : 'No sample documents available',
                docs: docs.length,
              }
            }),
          }
        }
      )
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
      var faculty = mock.assignedFaculty.find(function (f) {
        return f.id === facultyId
      })
      if (!faculty) return Promise.resolve(null)
      var assessment = mock.kraAssessments[facultyId] || { indicators: {} }
      var kras =
        global.FacultyLinkKraStructure && global.FacultyLinkKraStructure.buildReviewerKras
          ? global.FacultyLinkKraStructure.buildReviewerKras()
          : []
      kras.forEach(function (kra) {
        var kraKey = kra.title.split('—')[0].trim()
        kra.criteria.forEach(function (criterion) {
          criterion.indicators = criterion.indicators.map(function (indicator) {
            var record = assessment.indicators[kra.id + '/' + criterion.code + '/' + indicator.code] || {}
            return Object.assign({}, indicator, JSON.parse(JSON.stringify(record)), {
              documents: mock.documents.filter(function (d) {
                return d.facultyId === facultyId && d.kra === kraKey &&
                  d.criterion === criterion.code && d.indicator.split(' ')[0] === indicator.code
              }).map(function (d) {
                return { id: d.id, title: d.title, status: d.reviewStatus }
              }),
            })
          })
        })
      })
      return Promise.resolve({
        facultyId: faculty.id,
        facultyName: faculty.name,
        kras: kras,
      })
    },
    listEvaluationPeriods: function () {
      if (!global.FacultyLinkReviewerHttp) {
        return global.FacultyLinkEvaluationPeriods.ready().then(function () {
          return global.FacultyLinkEvaluationPeriods.list()
        })
      }
      return global.FacultyLinkReviewerHttp.reviewerFetch('/evaluation-periods').then(function (result) {
        if (!result.ok) throw new Error(result.body.message || 'Unable to load evaluation periods.')
        global.__facultylinkPeriodsFromServer = true
        global.FacultyLinkEvaluationPeriods.replaceAll(result.body.periods || [])
        return result.body.periods || []
      })
    },
    listEvaluationActivities: function () {
      var session = global.FacultyLinkMockAuth && global.FacultyLinkMockAuth.loadSession()
      var reviewerId = session && session.reviewerId ? session.reviewerId : 'R-01'
      return Promise.resolve(mock.evaluationActivities.filter(function (a) { return a.reviewerId === reviewerId }))
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
