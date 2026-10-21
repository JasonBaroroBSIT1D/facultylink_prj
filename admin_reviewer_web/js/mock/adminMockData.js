/**
 * MOCK DATA — visual testing only. Not official DBM–CHED scores or real records.
 */
(function (global) {
  global.FacultyLinkAdminMock = {
    dashboardSummary: {
      _mock: true,
      cards: [
        { label: 'Registered Faculty', value: '128', trend: '+6 this month', tone: 'blue' },
        { label: 'Active Reviewers', value: '14', trend: '2 pending invites', tone: 'cyan' },
        { label: 'Documents (7 days)', value: '342', trend: '89% auto-validated', tone: 'green' },
        { label: 'Needs Verification', value: '23', trend: 'Reviewer queue', tone: 'amber' },
        { label: 'Rank Simulations', value: '67', trend: 'Last 30 days', tone: 'navy' },
        { label: 'System Alerts', value: '5', trend: '3 configuration', tone: 'red' },
      ],
      recentActivity: [
        { time: '10:42 AM', text: 'Document auto-approved for Dr. Reyes — KRA II criterion B (mock).' },
        { time: '09:15 AM', text: 'Reviewer assigned to Dr. Santos — verification required (mock).' },
        { time: 'Yesterday', text: 'KRA IV indicator rules updated by admin (mock — not persisted).' },
      ],
    },
    faculty: [
      { id: 'F-001', name: 'Maria Clara Reyes', department: 'College of Engineering', rank: 'Assistant Professor III', status: 'Active', documents: 24, kraProgress: '72%' },
      { id: 'F-002', name: 'Juan Miguel Santos', department: 'College of Education', rank: 'Instructor I', status: 'Active', documents: 11, kraProgress: '41%' },
      { id: 'F-003', name: 'Elena V. Cruz', department: 'College of Arts & Sciences', rank: 'Associate Professor II', status: 'On leave', documents: 8, kraProgress: '58%' },
      { id: 'F-004', name: 'Roberto D. Lim', department: 'College of Business', rank: 'Assistant Professor I', status: 'Active', documents: 19, kraProgress: '65%' },
    ],
    reviewers: [
      { id: 'R-01', name: 'Prof. Ana Dela Peña', role: 'Senior Reviewer', assigned: 18, queue: 4, status: 'Active' },
      { id: 'R-02', name: 'Dr. Leo Fernandez', role: 'KRA Specialist', assigned: 12, queue: 2, status: 'Active' },
      { id: 'R-03', name: 'Prof. Grace Tan', role: 'Compliance Reviewer', assigned: 9, queue: 6, status: 'Active' },
    ],
    kraConfig: {
      _mock: true,
      get kras() {
        return global.FacultyLinkKraStructure
          ? FacultyLinkKraStructure.buildAdminKras()
          : []
      },
    },
    scoringRules: {
      _mock: true,
      validationRules: [
        { id: 'VR-01', name: 'PDF format & readability', type: 'Format', active: true, description: 'Reject unreadable scans (mock rule).' },
        { id: 'VR-02', name: 'Required metadata fields', type: 'Completeness', active: true, description: 'Title, date, signatory (mock).' },
        { id: 'VR-03', name: 'Duplicate document hash', type: 'Integrity', active: true, description: 'Flag matching file hashes (mock).' },
      ],
      scoringRules: [
        { id: 'SR-01', name: 'Indicator match confidence', type: 'OCR + rules', active: true, description: 'Threshold from backend engine (mock).' },
        { id: 'SR-02', name: 'Auto-approve when all mandatory pass', type: 'Workflow', active: true, description: 'System Approved without reviewer when eligible.' },
      ],
    },
    documentMonitoring: [
      { id: 'DOC-8821', faculty: 'Maria Clara Reyes', kra: 'KRA II', criterion: 'A', status: 'System Approved', uploaded: '2026-10-18', ocr: 'Complete' },
      { id: 'DOC-8819', faculty: 'Juan Miguel Santos', kra: 'KRA I', criterion: 'B', status: 'Needs Verification', uploaded: '2026-10-17', ocr: 'Complete' },
      { id: 'DOC-8812', faculty: 'Roberto D. Lim', kra: 'KRA IV', criterion: 'A', status: 'Needs Revision', uploaded: '2026-10-16', ocr: 'Partial' },
      { id: 'DOC-8804', faculty: 'Elena V. Cruz', kra: 'KRA III', criterion: 'A', status: 'Rejected', uploaded: '2026-10-15', ocr: 'Failed' },
    ],
    rankSimulation: [
      { faculty: 'Maria Clara Reyes', currentRank: 'Assistant Professor III', simulated: 'Associate Professor I', eligiblePts: '—', missing: '2 indicators (mock)', updated: '2026-10-19' },
      { faculty: 'Juan Miguel Santos', currentRank: 'Instructor I', simulated: 'Assistant Professor I', eligiblePts: '—', missing: 'SET/SEF aggregate (mock)', updated: '2026-10-18' },
    ],
    reports: {
      _mock: true,
      items: [
        { name: 'Faculty Document Throughput', period: 'Monthly', format: 'PDF / CSV', lastRun: 'Not run (mock)' },
        { name: 'KRA Progress Summary', period: 'Semester', format: 'PDF', lastRun: 'Not run (mock)' },
        { name: 'Reviewer Workload', period: 'Weekly', format: 'CSV', lastRun: 'Not run (mock)' },
        { name: 'Auto-Approval Rate', period: 'Quarterly', format: 'PDF', lastRun: 'Not run (mock)' },
      ],
    },
    notifications: [
      { id: 'N1', title: 'KRA II rules pending review', body: 'Configuration draft saved locally only (mock).', time: '2h ago', unread: true },
      { id: 'N2', title: '23 documents need verification', body: 'Queue assigned to reviewers (mock data).', time: '5h ago', unread: true },
      { id: 'N3', title: 'System maintenance window', body: 'Placeholder notification.', time: '1d ago', unread: false },
    ],
    settings: {
      _mock: true,
      institutionName: 'Sample State University (mock)',
      adminEmail: 'admin@facultylink.edu',
      timezone: 'Asia/Manila',
      ocrLanguage: 'eng',
      autoApproveEnabled: true,
    },
  }
})(window)
