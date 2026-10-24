import 'package:flutter_test/flutter_test.dart';
import 'package:facultylink_prj/models/document_status.dart';
import 'package:facultylink_prj/models/kra_configuration_models.dart';
import 'package:facultylink_prj/services/api/faculty_document_parser.dart';

void main() {
  test('maps API document with extraction and validation', () {
    final config = KraConfigurationBundle.fromJson({
      'kras': [
        {
          'kra_id': 9,
          'code': 'KRA I',
          'name': 'Instruction',
          'criteria': [
            {
              'criterion_id': 9,
              'code': 'A',
              'name': 'Teaching',
              'indicators': [
                {'indicator_id': 9, 'code': 'A.1', 'name': 'SET'},
              ],
            },
          ],
        },
      ],
    });

    final detail = FacultyDocumentParser.fromDetailJson({
      'id': '42',
      'documentId': 42,
      'criterionId': 9,
      'indicatorId': 9,
      'title': 'SET Report',
      'originalFilename': 'set.pdf',
      'status': 'needs_verification',
      'uploadedAt': '2026-10-24T10:00:00+00:00',
      'extraction': {
        'status': 'completed',
        'ocrConfidence': 92.0,
        'extractionMethod': 'pypdf_text',
        'extractedText': 'Overall SET Rating: 88',
        'extractedFields': {
          'faculty_name': 'Demo Faculty',
          'overall_rating': 88,
          'classified_indicator_code': 'A.1',
        },
      },
      'validation': {
        'result': 'needs_verification',
        'explanation': 'Reviewer verification required.',
        'ruleVersion': 'phase2.1',
        'checks': {
          'items': [
            {'name': 'rating_range', 'passed': true, 'message': 'OK'},
          ],
        },
      },
    }, config);

    expect(detail.status.label, 'Needs Verification');
    expect(detail.detectedIndicator, contains('A.1'));
    expect(detail.ocrFields.any((e) => e.key == 'faculty_name'), isTrue);
    expect(detail.validationChecks.single.passed, isTrue);
  });
}
