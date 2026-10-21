import '../../core/kra/kra_structure.dart';
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

  static final kraOverview = [
    KraOverviewItem(id: 'kra1', title: KraStructure.kraTitles[KraStructure.kraI]!, status: 'In progress', progress: 0.65),
    KraOverviewItem(id: 'kra2', title: KraStructure.kraTitles[KraStructure.kraII]!, status: 'Documents pending', progress: 0.42),
    KraOverviewItem(id: 'kra3', title: KraStructure.kraTitles[KraStructure.kraIII]!, status: 'Not started', progress: 0.15),
    KraOverviewItem(id: 'kra4', title: KraStructure.kraTitles[KraStructure.kraIV]!, status: 'In progress', progress: 0.55),
  ];

  static const recentActivity = [
    ActivityItem(time: 'Today', message: 'Publication PDF — System Approved (mock rule engine).'),
    ActivityItem(time: 'Yesterday', message: 'Syllabus upload — Needs Verification (mock).'),
    ActivityItem(time: 'Oct 18', message: 'Reviewer comment on extension MOA (mock).'),
  ];

  static final documents = [
    FacultyDocument(
      id: 'd1',
      title: 'Journal Article — Adaptive Learning',
      fileName: 'journal_article.pdf',
      uploadedAt: DateTime(2026, 10, 18),
      kra: KraStructure.kraII,
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
      kra: KraStructure.kraI,
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
      kra: KraStructure.kraI,
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
      extractedText: 'Mock OCR excerpt for ${base.fileName}. Full text from Tesseract via Flask backend.',
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

  static KraIndicatorMock _placeholderIndicator(String code) => KraIndicatorMock(
        code: code,
        title: 'Indicator $code (config TBD)',
        evidence: const ['Supporting document'],
        aggregatedScore: 'Not Yet Calculated',
      );

  static KraCriterionMock _placeholderCriterion(String letter) => KraCriterionMock(
        code: letter,
        title: 'Criterion $letter',
        indicators: [_placeholderIndicator('$letter.1')],
      );

  static List<KraSectionMock> get kraSections {
    KraCriterionMock kra1A = KraCriterionMock(
      code: 'A',
      title: 'Criterion A — Teaching Effectiveness',
      indicators: const [
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
    );
    KraCriterionMock kra1B = KraCriterionMock(
      code: 'B',
      title: 'Criterion B — Load-related (placeholder)',
      indicators: [
        KraIndicatorMock(code: 'B.1', title: 'Teaching load (config TBD)', evidence: ['Load form']),
      ],
    );

    KraCriterionMock kra2A = KraCriterionMock(
      code: 'A',
      title: 'Criterion A — Research output (placeholder)',
      indicators: [
        KraIndicatorMock(code: 'A.1', title: 'Publication (config TBD)', evidence: ['PDF']),
      ],
    );

    KraCriterionMock kra3A = KraCriterionMock(
      code: 'A',
      title: 'Criterion A — Extension (placeholder)',
      indicators: [
        KraIndicatorMock(code: 'A.1', title: 'Extension project (config TBD)', evidence: ['MOA']),
      ],
    );

    KraCriterionMock kra4A = KraCriterionMock(
      code: 'A',
      title: 'Criterion A — Qualifications (placeholder)',
      indicators: [
        KraIndicatorMock(code: 'A.1', title: 'Graduate degree (config TBD)', evidence: ['Diploma']),
      ],
    );

    List<KraCriterionMock> criteriaFor(String kra, Map<String, KraCriterionMock> seeded) {
      return KraStructure.lettersFor(kra).map((letter) {
        return seeded[letter] ?? _placeholderCriterion(letter);
      }).toList();
    }

    return [
      KraSectionMock(
        id: 'kra1',
        title: KraStructure.kraTitles[KraStructure.kraI]!,
        criteria: criteriaFor(KraStructure.kraI, {'A': kra1A, 'B': kra1B}),
      ),
      KraSectionMock(
        id: 'kra2',
        title: KraStructure.kraTitles[KraStructure.kraII]!,
        criteria: criteriaFor(KraStructure.kraII, {'A': kra2A}),
      ),
      KraSectionMock(
        id: 'kra3',
        title: KraStructure.kraTitles[KraStructure.kraIII]!,
        criteria: criteriaFor(KraStructure.kraIII, {'A': kra3A}),
      ),
      KraSectionMock(
        id: 'kra4',
        title: KraStructure.kraTitles[KraStructure.kraIV]!,
        criteria: criteriaFor(KraStructure.kraIV, {'A': kra4A}),
      ),
    ];
  }

  static Map<String, List<String>> get criterionOptions {
    final map = <String, List<String>>{};
    for (final kra in KraStructure.kraOptions) {
      map[kra] = KraStructure.lettersFor(kra);
    }
    return map;
  }
}
