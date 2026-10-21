/**
 * MOCK DATA — Reviewer portal UI testing only.
 * KRA hierarchy follows DBM–CHED structure (illustrative placeholders where config TBD).
 */
(function (global) {
  var SAMPLE_PDF =
    'https://www.w3.org/WAI/WCAG21/Techniques/pdf/img/table-word.pdf'

  global.FacultyLinkReviewerMock = {
    dashboard: {
      cards: [
        { label: 'Assigned Faculty', value: '12', tone: 'blue' },
        { label: 'Needs Verification', value: '8', tone: 'amber' },
        { label: 'Needs Revision', value: '3', tone: 'warning' },
        { label: 'Reviewed (30d)', value: '47', tone: 'green' },
        { label: 'Pending Assessment Issues', value: '2', tone: 'red' },
      ],
      recentActivity: [
        { time: '11:05 AM', text: 'Inspected system-approved publication — no override (mock).' },
        { time: '09:40 AM', text: 'Requested revision on incomplete MOA — KRA III (mock).' },
        { time: 'Yesterday', text: 'Verified SET aggregation display for Dr. Reyes — KRA I-A.1 (mock).' },
      ],
      attention: [
        { id: 'DOC-8819', faculty: 'Juan Miguel Santos', title: 'Syllabus — CS 101', status: 'Needs Verification' },
        { id: 'DOC-8804', faculty: 'Elena V. Cruz', title: 'Extension report', status: 'Rejected' },
      ],
    },
    assignedFaculty: [
      {
        id: 'F-001',
        name: 'Maria Clara Reyes',
        department: 'College of Engineering',
        rank: 'Assistant Professor III',
        status: 'In progress',
        documents: 24,
      },
      {
        id: 'F-002',
        name: 'Juan Miguel Santos',
        department: 'College of Education',
        rank: 'Instructor I',
        status: 'Verification pending',
        documents: 11,
      },
      {
        id: 'F-004',
        name: 'Roberto D. Lim',
        department: 'College of Business',
        rank: 'Assistant Professor I',
        status: 'In progress',
        documents: 19,
      },
    ],
    facultyOverview: {
      'F-001': {
        name: 'Maria Clara Reyes',
        kraSummary: [
          { kra: 'KRA I', progress: 'Criterion A under review (SET/SEF indicators)', docs: 8 },
          { kra: 'KRA II', progress: 'Research outputs — mostly system approved', docs: 6 },
          { kra: 'KRA III', progress: 'Extension evidence uploaded', docs: 4 },
          { kra: 'KRA IV', progress: 'Qualifications complete (mock)', docs: 6 },
        ],
      },
    },
    documents: [
      {
        id: 'DOC-8821',
        facultyId: 'F-001',
        faculty: 'Maria Clara Reyes',
        title: 'Peer-reviewed journal article',
        fileType: 'PDF',
        kra: 'KRA II',
        criterion: 'A',
        indicator: 'A.1 Publication (illustrative)',
        uploaded: '2026-10-18',
        validationStatus: 'Passed mandatory rules',
        reviewStatus: 'System Approved',
        previewUrl: SAMPLE_PDF,
        ocr: {
          text: '… FacultyLink mock OCR excerpt: Journal of Engineering Education, Vol. 12 …',
          fields: [
            { label: 'Document title', value: 'Adaptive Learning Modules', confidence: '92%' },
            { label: 'Publication year', value: '2025', confidence: '88%' },
          ],
          gaps: ['Author affiliation line uncertain (mock).'],
        },
        validation: {
          checks: [
            { name: 'Identity matching', result: 'pass', detail: 'Faculty name match (mock).' },
            { name: 'Document classification', result: 'pass', detail: 'Classified as publication (mock).' },
            { name: 'Evidence completeness', result: 'pass', detail: 'Required fields present (mock).' },
            { name: 'Duplicate detection', result: 'pass', detail: 'No duplicate hash (mock).' },
            { name: 'Eligibility checks', result: 'pass', detail: 'Eligible indicator (mock).' },
          ],
          overall: 'All mandatory rules satisfied — eligible for System Approved.',
          needsVerificationReason: null,
        },
        reviewer: {
          authorized: true,
          note: 'Inspection only — document already system approved.',
        },
      },
      {
        id: 'DOC-8819',
        facultyId: 'F-002',
        faculty: 'Juan Miguel Santos',
        title: 'Course syllabus — EDUC 210',
        fileType: 'PDF',
        kra: 'KRA I',
        criterion: 'B',
        indicator: 'B.1 Load-related (illustrative)',
        uploaded: '2026-10-17',
        validationStatus: 'Rule warnings',
        reviewStatus: 'Needs Verification',
        previewUrl: SAMPLE_PDF,
        ocr: {
          text: '… Syllabus EDUC 210 … contact hours …',
          fields: [{ label: 'Course code', value: 'EDUC 210', confidence: '95%' }],
          gaps: ['Dean signature not detected (mock).'],
        },
        validation: {
          checks: [
            { name: 'Identity matching', result: 'pass', detail: 'Match (mock).' },
            { name: 'Evidence completeness', result: 'warn', detail: 'Signatory field missing (mock).' },
            { name: 'Duplicate detection', result: 'pass', detail: 'Unique (mock).' },
          ],
          overall: 'Mandatory checks incomplete — verification required.',
          needsVerificationReason: 'Missing authorized signatory on syllabus (mock finding).',
        },
        reviewer: { authorized: true, note: 'Reviewer may approve, reject, or request revision when API connected.' },
      },
    ],
    kraAssessment: {
      facultyId: 'F-001',
      facultyName: 'Maria Clara Reyes',
      get kras() {
        return global.FacultyLinkKraStructure
          ? FacultyLinkKraStructure.buildReviewerKras()
          : []
      },
    },
    rankSimulation: [
      {
        facultyId: 'F-001',
        faculty: 'Maria Clara Reyes',
        currentRank: 'Assistant Professor III',
        kra1: 'Awaiting Backend Evaluation',
        kra2: 'Awaiting Backend Evaluation',
        kra3: 'Awaiting Backend Evaluation',
        kra4: 'Awaiting Backend Evaluation',
        totalPoints: 'Not Yet Calculated',
        simulatedRank: 'Not Yet Calculated',
        missing: 'Backend rank simulation pending (mock).',
        status: 'Advisory preview only',
      },
    ],
    evaluationHistory: [
      {
        faculty: 'Juan Miguel Santos',
        item: 'DOC-8819 — Syllabus',
        kra: 'KRA I / B / B.1',
        previous: 'Submitted',
        updated: 'Needs Verification',
        action: 'Flagged for signatory check',
        remarks: 'Mock audit entry',
        when: '2026-10-17 09:40',
      },
      {
        faculty: 'Maria Clara Reyes',
        item: 'DOC-8821 — Publication',
        kra: 'KRA II / A / A.1',
        previous: 'Validating',
        updated: 'System Approved',
        action: 'Auto-approved by rule engine',
        remarks: 'No mandatory reviewer step (mock)',
        when: '2026-10-18 10:42',
      },
    ],
    notifications: [
      { id: 'RN1', title: '8 documents need verification', body: 'Mock queue summary.', time: '1h ago', unread: true },
      { id: 'RN2', title: 'Revision submitted', body: 'Dr. Cruz re-upload pending (mock).', time: '3h ago', unread: true },
      { id: 'RN3', title: 'New faculty assignment', body: 'Roberto D. Lim added (mock).', time: '1d ago', unread: false },
    ],
    settings: {
      name: 'Faculty Reviewer',
      email: 'reviewer@facultylink.edu',
      department: 'Office of Faculty Affairs (mock)',
      notifyVerification: true,
      notifyRevision: true,
    },
  }
})(window)
