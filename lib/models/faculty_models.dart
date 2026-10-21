import 'document_status.dart';

class FacultyProfile {
  const FacultyProfile({
    required this.id,
    required this.fullName,
    required this.email,
    required this.department,
    required this.college,
    required this.rank,
  });

  final String id;
  final String fullName;
  final String email;
  final String department;
  final String college;
  final String rank;
}

class DashboardSummary {
  const DashboardSummary({
    required this.totalDocuments,
    required this.systemApproved,
    required this.needsVerification,
    required this.needsRevision,
    required this.kraProgressPercent,
  });

  final int totalDocuments;
  final int systemApproved;
  final int needsVerification;
  final int needsRevision;
  final int kraProgressPercent;
}

class KraOverviewItem {
  const KraOverviewItem({
    required this.id,
    required this.title,
    required this.status,
    required this.progress,
    this.eligiblePointsLabel = 'Awaiting backend',
  });

  final String id;
  final String title;
  final String status;
  final double progress;
  final String eligiblePointsLabel;
}

class ActivityItem {
  const ActivityItem({required this.time, required this.message});

  final String time;
  final String message;
}

class FacultyDocument {
  const FacultyDocument({
    required this.id,
    required this.title,
    required this.fileName,
    required this.uploadedAt,
    required this.kra,
    required this.criterion,
    this.detectedIndicator,
    required this.status,
    required this.ocrStatus,
    this.reviewerNote,
  });

  final String id;
  final String title;
  final String fileName;
  final DateTime uploadedAt;
  final String kra;
  final String criterion;
  final String? detectedIndicator;
  final DocumentStatus status;
  final String ocrStatus;
  final String? reviewerNote;
}

class ValidationCheck {
  const ValidationCheck({
    required this.name,
    required this.passed,
    required this.explanation,
  });

  final String name;
  final bool passed;
  final String explanation;
}

class DocumentDetail extends FacultyDocument {
  const DocumentDetail({
    required super.id,
    required super.title,
    required super.fileName,
    required super.uploadedAt,
    required super.kra,
    required super.criterion,
    super.detectedIndicator,
    required super.status,
    required super.ocrStatus,
    super.reviewerNote,
    required this.extractedText,
    required this.ocrFields,
    required this.ocrGaps,
    required this.validationChecks,
    required this.validationSummary,
    required this.statusHistory,
  });

  final String extractedText;
  final List<MapEntry<String, String>> ocrFields;
  final List<String> ocrGaps;
  final List<ValidationCheck> validationChecks;
  final String validationSummary;
  final List<MapEntry<String, String>> statusHistory;
}

class AppNotification {
  const AppNotification({
    required this.id,
    required this.title,
    required this.body,
    required this.time,
    required this.read,
    required this.type,
  });

  final String id;
  final String title;
  final String body;
  final String time;
  final bool read;
  final String type;
}

class RankSimulationView {
  const RankSimulationView({
    required this.currentRank,
    required this.assessmentPeriod,
    required this.assessmentStatus,
    required this.kraScores,
    required this.totalEligiblePoints,
    required this.simulatedRank,
    required this.missingRequirements,
    required this.readinessStatus,
  });

  final String currentRank;
  final String assessmentPeriod;
  final String assessmentStatus;
  final List<MapEntry<String, String>> kraScores;
  final String totalEligiblePoints;
  final String simulatedRank;
  final List<String> missingRequirements;
  final String readinessStatus;
}

class KraIndicatorMock {
  const KraIndicatorMock({
    required this.code,
    required this.title,
    required this.evidence,
    this.semesters = const [],
    this.aggregatedScore = 'Not Yet Calculated',
  });

  final String code;
  final String title;
  final List<String> evidence;
  final List<String> semesters;
  final String aggregatedScore;
}

class KraCriterionMock {
  const KraCriterionMock({
    required this.code,
    required this.title,
    required this.indicators,
  });

  final String code;
  final String title;
  final List<KraIndicatorMock> indicators;
}

class KraSectionMock {
  const KraSectionMock({
    required this.id,
    required this.title,
    required this.criteria,
  });

  final String id;
  final String title;
  final List<KraCriterionMock> criteria;
}
