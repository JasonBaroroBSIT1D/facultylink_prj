import '../../models/document_status.dart';
import '../../models/faculty_models.dart';

/// Mock data for faculty mobile UI — not official DBM–CHED outcomes.
abstract final class FacultyMockData {
  static const mockBanner =
      'Mock data — scores and approvals are illustrative until Flask API integration.';

  static const profile = FacultyProfile(
    id: 'F-2024-0142',
    fullName: 'Maria Clara Reyes',
    email: 'm.reyes@facultylink.edu',
    department: 'Computer Engineering',
    college: 'College of Engineering',
    rank: 'Assistant Professor III',
  );

  static const dashboardSummary = DashboardSummary(
    totalDocuments: 18,
    systemApproved: 11,
    needsVerification: 4,
    needsRevision: 2,
    kraProgressPercent: 58,
  );

  static const kraOverview = [
    KraOverviewItem(
      id: 'kra1',
      title: 'KRA I — Instruction',
      status: 'In progress',
      progress: 0.65,
    ),
    KraOverviewItem(
      id: 'kra2',
      title: 'KRA II — Research and Innovation',
      status: 'Documents pending',
      progress: 0.42,
    ),
    KraOverviewItem(
      id: 'kra3',
      title: 'KRA III — Extension or Community Services',
      status: 'Not started',
      progress: 0.15,
    ),
    KraOverviewItem(
      id: 'kra4',
      title: 'KRA IV — Professional Development',
      status: 'In progress',
      progress: 0.55,
    ),
  ];

  static const recentActivity = [
    ActivityItem(
      time: 'Today',
      message: 'Publication PDF — System Approved (mock rule engine).',
    ),
    ActivityItem(
      time: 'Yesterday',
      message: 'Syllabus upload — Needs Verification (mock).',
    ),
    ActivityItem(
      time: 'Oct 18',
      message: 'Reviewer comment on extension MOA (mock).',
    ),
  ];

  static final documents = [
    FacultyDocument(
      id: 'd1',
      title: 'Journal Article — Adaptive Learning',
      fileName: 'journal_article.pdf',
      uploadedAt: DateTime(2026, 10, 18),
      kra: 'KRA II',
      criterion: 'A',
      detectedIndicator: 'A.1 Publication (classified mock)',
      status: DocumentStatus.systemApproved,
      ocrStatus: 'Complete',
    ),
    FacultyDocument(
      id: 'd2',
      title: 'Course Syllabus EDUC 210',
      fileName: 'syllabus_educ210.pdf',
      uploadedAt: DateTime(2026, 10, 17),
      kra: 'KRA I',
      criterion: 'B',
      detectedIndicator: 'B.1 Load (mock)',
      status: DocumentStatus.needsVerification,
      ocrStatus: 'Complete',
      reviewerNote: 'Signatory verification pending (mock).',
    ),
    FacultyDocument(
      id: 'd3',
      title: 'SET Summary AY 2024–2025',
      fileName: 'set_summary.pdf',
      uploadedAt: DateTime(2026, 10, 10),
      kra: 'KRA I',
      criterion: 'A',
      detectedIndicator: 'A.1 Student Evaluation (SET)',
      status: DocumentStatus.validating,
      ocrStatus: 'Processing',
    ),
  ];

  static DocumentDetail detailFor(String id) {
    final base = documents.firstWhere((d) => d.id == id, orElse: () => documents.first);
    return DocumentDetail(
      id: base.id,
      title: base.title,
      fileName: base.fileName,
      uploadedAt: base.uploadedAt,
      kra: base.kra,
      criterion: base.criterion,
      detectedIndicator: base.detectedIndicator,
      status: base.status,
      ocrStatus: base.ocrStatus,
      reviewerNote: base.reviewerNote,
      extractedText:
          'Mock OCR excerpt for ${base.fileName}. Full text from Tesseract via Flask backend.',
      ocrFields: const [
        MapEntry('Title', 'Sample extracted title'),
        MapEntry('Date', '2025-08-01'),
      ],
      ocrGaps: const ['Author block uncertain (mock).'],
      validationChecks: [
        ValidationCheck(
          name: 'KRA / Criterion alignment',
          passed: base.status != DocumentStatus.rejected,
          explanation: 'Selected KRA and criterion match classification (mock).',
        ),
        ValidationCheck(
          name: 'Evidence completeness',
          passed: base.status == DocumentStatus.systemApproved,
          explanation: 'Required fields check via rule engine (mock).',
        ),
        ValidationCheck(
          name: 'Duplicate detection',
          passed: true,
          explanation: 'No duplicate hash (mock).',
        ),
      ],
      validationSummary: base.status == DocumentStatus.systemApproved
          ? 'All mandatory rules passed — System Approved without mandatory reviewer step.'
          : 'Verification or revision may be required — see checks above (mock).',
      statusHistory: [
        MapEntry('Uploaded', base.uploadedAt.toString().split(' ').first),
        MapEntry('Current', base.status.label),
      ],
    );
  }

  static const notifications = [
    AppNotification(
      id: 'n1',
      title: 'Document System Approved',
      body: 'Journal Article passed validation (mock).',
      time: '2h ago',
      read: false,
      type: 'approval',
    ),
    AppNotification(
      id: 'n2',
      title: 'Needs Verification',
      body: 'Syllabus awaiting reviewer (mock).',
      time: '1d ago',
      read: false,
      type: 'verification',
    ),
    AppNotification(
      id: 'n3',
      title: 'OCR processing completed',
      body: 'SET summary text extracted (mock).',
      time: '3d ago',
      read: true,
      type: 'ocr',
    ),
  ];

  static const rankSimulation = RankSimulationView(
    currentRank: 'Assistant Professor III',
    assessmentPeriod: 'AY 2025–2026 (mock)',
    assessmentStatus: 'Advisory self-assessment',
    kraScores: [
      MapEntry('KRA I', 'Awaiting Evaluation'),
      MapEntry('KRA II', 'Awaiting Evaluation'),
      MapEntry('KRA III', 'Not Yet Calculated'),
      MapEntry('KRA IV', 'Awaiting Evaluation'),
    ],
    totalEligiblePoints: 'Not Yet Calculated',
    simulatedRank: 'No Verified Scores Available',
    missingRequirements: [
      'Backend rank simulation not connected.',
      'Complete KRA III extension evidence (mock gap).',
    ],
    readinessStatus: 'Awaiting backend evaluation',
  );

  static const kraSections = [
    KraSectionMock(
      id: 'kra1',
      title: 'KRA I — Instruction',
      criteria: [
        KraCriterionMock(
          code: 'A',
          title: 'Criterion A — Teaching Effectiveness',
          indicators: [
            KraIndicatorMock(
              code: 'A.1',
              title: 'Student Evaluation (SET)',
              evidence: ['SET reports', 'Consolidated SET PDFs'],
              semesters: [
                '1st Sem AY 2024–2025 — rating: backend aggregation pending',
                '2nd Sem AY 2024–2025 — rating: backend aggregation pending',
              ],
            ),
            KraIndicatorMock(
              code: 'A.2',
              title: 'Supervisor Evaluation (SEF)',
              evidence: ['SEF summary sheets'],
              semesters: ['1st Sem AY 2024–2025 — backend aggregation pending'],
            ),
          ],
        ),
        KraCriterionMock(
          code: 'B',
          title: 'Criterion B — Load-related (placeholder)',
          indicators: [
            KraIndicatorMock(code: 'B.1', title: 'Teaching load (config TBD)', evidence: ['Load form']),
          ],
        ),
      ],
    ),
    KraSectionMock(
      id: 'kra2',
      title: 'KRA II — Research and Innovation',
      criteria: [
        KraCriterionMock(
          code: 'A',
          title: 'Criterion A — Research output (placeholder)',
          indicators: [
            KraIndicatorMock(code: 'A.1', title: 'Publication (config TBD)', evidence: ['PDF']),
          ],
        ),
      ],
    ),
    KraSectionMock(
      id: 'kra3',
      title: 'KRA III — Extension or Community Services',
      criteria: [
        KraCriterionMock(
          code: 'A',
          title: 'Criterion A — Extension (placeholder)',
          indicators: [
            KraIndicatorMock(code: 'A.1', title: 'Extension project (config TBD)', evidence: ['MOA']),
          ],
        ),
      ],
    ),
    KraSectionMock(
      id: 'kra4',
      title: 'KRA IV — Professional Development',
      criteria: [
        KraCriterionMock(
          code: 'A',
          title: 'Criterion A — Qualifications (placeholder)',
          indicators: [
            KraIndicatorMock(code: 'A.1', title: 'Graduate degree (config TBD)', evidence: ['Diploma']),
          ],
        ),
      ],
    ),
  ];

  static const kraOptions = ['KRA I', 'KRA II', 'KRA III', 'KRA IV'];

  static Map<String, List<String>> criterionOptions = {
    'KRA I': ['A — Teaching Effectiveness', 'B — Load-related'],
    'KRA II': ['A — Research output'],
    'KRA III': ['A — Extension'],
    'KRA IV': ['A — Qualifications'],
  };
}
