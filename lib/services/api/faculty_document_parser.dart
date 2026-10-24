import '../../models/document_status.dart';
import '../../models/faculty_models.dart';
import '../../models/kra_configuration_models.dart';

abstract final class FacultyDocumentParser {
  static DocumentStatus statusFromApi(String? raw) {
    switch (raw) {
      case 'system_approved':
        return DocumentStatus.systemApproved;
      case 'needs_verification':
        return DocumentStatus.needsVerification;
      case 'needs_revision':
        return DocumentStatus.needsRevision;
      case 'rejected':
        return DocumentStatus.rejected;
      case 'upload_failed':
        return DocumentStatus.uploadFailed;
      case 'processing':
        return DocumentStatus.validating;
      case 'uploaded':
        return DocumentStatus.ocrProcessing;
      default:
        return DocumentStatus.needsVerification;
    }
  }

  static FacultyDocument fromListJson(
    Map<String, dynamic> json,
    KraConfigurationBundle config,
  ) {
    final criterionId = json['criterionId'] as int?;
    final target = config.criterionForId(criterionId);
    final indicatorId = json['indicatorId'] as int?;
    final classified = config.indicatorLabelFor(indicatorId);
    final uploadedRaw = json['uploadedAt'] as String?;
    return FacultyDocument(
      id: json['id'] as String? ?? '${json['documentId']}',
      title: json['title'] as String? ?? 'Document',
      fileName: json['originalFilename'] as String? ?? '',
      uploadedAt: uploadedRaw != null
          ? DateTime.parse(uploadedRaw)
          : DateTime.now(),
      kra: target?.kraCode ?? 'KRA',
      criterion: target?.criterionCode ?? '?',
      detectedIndicator: classified,
      status: statusFromApi(json['status'] as String?),
      ocrStatus: json['status'] == 'processing' ? 'Processing' : 'Recorded',
    );
  }

  static DocumentDetail fromDetailJson(
    Map<String, dynamic> json,
    KraConfigurationBundle config,
  ) {
    final base = fromListJson(json, config);
    final extraction = json['extraction'] as Map<String, dynamic>?;
    final validation = json['validation'] as Map<String, dynamic>?;

    final fields = extraction?['extractedFields'] as Map<String, dynamic>? ?? {};
    final ocrFields = <MapEntry<String, String>>[];
    final gaps = <String>[];

    const skipKeys = {
      'classified_indicator_code',
      'classification_scores',
      'extraction_method',
      'ocr_page_methods',
      'ocr_details',
      '_field_confidence',
    };

    for (final entry in fields.entries) {
      if (entry.key.startsWith('_') || skipKeys.contains(entry.key)) continue;
      ocrFields.add(MapEntry(entry.key, '${entry.value}'));
    }

    final fieldConf = fields['_field_confidence'];
    if (fieldConf is Map) {
      for (final e in fieldConf.entries) {
        final v = e.value;
        if (v is num && v < 0.6) {
          gaps.add('${e.key}: low extraction confidence (${v.toStringAsFixed(2)})');
        }
      }
    }

    final classifiedCode = fields['classified_indicator_code'] as String?;
    final indicatorLabel = base.detectedIndicator ??
        (classifiedCode != null
            ? 'Indicator $classifiedCode (SET/SEF classification)'
            : null);

    final checksRaw = validation?['checks'];
    final items = checksRaw is Map
        ? (checksRaw['items'] as List<dynamic>? ?? [])
        : (checksRaw as List<dynamic>? ?? []);

    final checks = items.map((c) {
      final m = c as Map<String, dynamic>;
      return ValidationCheck(
        name: _humanizeCheckName(m['name'] as String? ?? ''),
        passed: m['passed'] == true,
        explanation: m['message'] as String? ?? '',
      );
    }).toList();

    final ocrConf = extraction?['ocrConfidence'];
    final method = extraction?['extractionMethod'] as String?;
    var ocrStatus = extraction?['status'] as String? ?? 'completed';
    if (ocrConf != null) {
      ocrStatus = '$ocrStatus · OCR ${(ocrConf as num).toStringAsFixed(0)}%'
          '${method != null ? ' · $method' : ''}';
    }

    return DocumentDetail(
      id: base.id,
      title: base.title,
      fileName: base.fileName,
      uploadedAt: base.uploadedAt,
      kra: base.kra,
      criterion: base.criterion,
      detectedIndicator: indicatorLabel,
      status: base.status,
      ocrStatus: ocrStatus,
      reviewerNote: null,
      extractedText: extraction?['extractedText'] as String? ?? '',
      ocrFields: ocrFields,
      ocrGaps: gaps,
      validationChecks: checks,
      validationSummary: validation?['explanation'] as String? ??
          'Validation pending or unavailable.',
      statusHistory: [
        MapEntry('Uploaded', base.uploadedAt.toIso8601String()),
        MapEntry('Status', base.status.label),
        if (validation?['result'] != null)
          MapEntry('Validation', '${validation!['result']}'),
        if (validation?['ruleVersion'] != null)
          MapEntry('Rule version', '${validation!['ruleVersion']}'),
      ],
    );
  }

  static String _humanizeCheckName(String name) {
    return name
        .replaceAll('_', ' ')
        .split(' ')
        .map((w) => w.isEmpty ? w : '${w[0].toUpperCase()}${w.substring(1)}')
        .join(' ');
  }
}
