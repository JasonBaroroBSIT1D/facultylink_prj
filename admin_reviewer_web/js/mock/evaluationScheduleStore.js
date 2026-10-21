/**
 * Shared frontend demonstration state for evaluation schedules.
 */
(function (global) {
  var schedules = [
    {
      id: 'ES-001',
      academicYear: 'AY 2025–2026',
      semester: '1st Semester',
      type: 'KRA Document Review',
      faculty: 'Maria Clara Reyes',
      facultyId: 'F-001',
      reviewer: 'Prof. Ana Dela Peña',
      reviewerId: 'R-01',
      date: '2026-10-28',
      time: '09:00',
      status: 'Scheduled',
      location: 'Faculty Affairs Conference Room',
      notes: 'Initial KRA I–II document verification session.',
    },
    {
      id: 'ES-002',
      academicYear: 'AY 2025–2026',
      semester: '1st Semester',
      type: 'Rank Simulation Briefing',
      faculty: 'Juan Miguel Santos',
      facultyId: 'F-002',
      reviewer: 'Dr. Leo Fernandez',
      reviewerId: 'R-02',
      date: '2026-10-30',
      time: '14:00',
      status: 'Scheduled',
      location: 'Virtual — MS Teams',
      notes: 'Advisory rank simulation walkthrough (sample data).',
    },
    {
      id: 'ES-003',
      academicYear: 'AY 2025–2026',
      semester: '2nd Semester',
      type: 'Extension Evidence Review',
      faculty: 'Elena V. Cruz',
      facultyId: 'F-003',
      reviewer: 'Prof. Grace Tan',
      reviewerId: 'R-03',
      date: '2026-11-05',
      time: '10:30',
      status: 'Pending',
      location: 'College of Arts & Sciences',
      notes: 'KRA III criterion review.',
    },
  ]

  function clone(list) {
    return list.map(function (s) {
      return Object.assign({}, s)
    })
  }

  global.FacultyLinkEvaluationSchedule = {
    list: function () {
      return clone(schedules)
    },
    listForReviewer: function (reviewerId) {
      return clone(
        schedules.filter(function (s) {
          return s.status !== 'Cancelled' && (!reviewerId || s.reviewerId === reviewerId)
        })
      )
    },
    add: function (entry) {
      var id = 'ES-' + String(100 + schedules.length + 1)
      var row = Object.assign({ id: id, status: entry.status || 'Scheduled' }, entry)
      schedules.push(row)
      return row
    },
    update: function (id, patch) {
      var idx = schedules.findIndex(function (s) {
        return s.id === id
      })
      if (idx === -1) return null
      schedules[idx] = Object.assign({}, schedules[idx], patch)
      return schedules[idx]
    },
    cancel: function (id) {
      return this.update(id, { status: 'Cancelled' })
    },
    get: function (id) {
      var row = schedules.find(function (s) {
        return s.id === id
      })
      return row ? Object.assign({}, row) : null
    },
  }
})(window)
