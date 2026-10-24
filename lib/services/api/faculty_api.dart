import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart' show MediaType;

import '../../core/config/api_config.dart';
import '../../models/evaluation_period.dart';
import '../../models/faculty_models.dart';
import '../../models/kra_configuration_models.dart';
import '../auth/auth_session.dart';
import '../mock/faculty_mock_data.dart';
import 'faculty_api_exception.dart';
import 'faculty_document_parser.dart';

/// Faculty mobile API — evaluation periods and documents use Flask when authenticated.
abstract final class FacultyApi {
  /// Legacy mock flag for dashboard, profile, notifications, rank simulation.
  static bool useMock = true;

  /// Document list/upload/detail always use Flask (Phase 2.1 integration).
  static bool useMockDocuments = false;

  /// When true, load bundled JSON for evaluation periods (tests / offline dev only).
  static bool useBundledEvaluationPeriods = false;

  static KraConfigurationBundle? _kraCache;

  static Uri _uri(String path) => Uri.parse('${ApiConfig.baseUrl}$path');

  static Future<String?> _bearer() => AuthSession.instance.readToken();

  static Future<Map<String, String>> _authHeaders() async {
    final token = await _bearer();
    if (token == null || token.isEmpty) {
      throw FacultyApiException(
        'Sign in to continue.',
        errorCode: 'auth',
        statusCode: 401,
      );
    }
    return {
      'Accept': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  static Future<Map<String, dynamic>> _decodeJson(http.Response response) async {
    try {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      throw FacultyApiException(
        'Unexpected server response.',
        statusCode: response.statusCode,
      );
    }
  }

  static Future<List<EvaluationPeriod>> getEvaluationPeriods() async {
    if (useBundledEvaluationPeriods) {
      return _loadBundledPeriods();
    }

    final headers = await _authHeaders();
    http.Response response;
    try {
      response = await http.get(_uri('/api/v1/evaluation-periods'), headers: headers);
    } catch (_) {
      throw FacultyApiException(
        'Network error while loading evaluation periods.',
        errorCode: 'network',
      );
    }

    final body = await _decodeJson(response);
    if (response.statusCode != 200) {
      throw FacultyApiException(
        body['message'] as String? ?? 'Unable to load evaluation periods.',
        statusCode: response.statusCode,
      );
    }

    final rows = body['periods'] as List<dynamic>? ?? [];
    return rows
        .map((p) => EvaluationPeriod.fromJson(p as Map<String, dynamic>))
        .toList();
  }

  static Future<KraConfigurationBundle> getKraConfiguration({bool force = false}) async {
    if (!force && _kraCache != null) return _kraCache!;
    final headers = await _authHeaders();
    http.Response response;
    try {
      response = await http.get(_uri('/api/v1/kra-configuration'), headers: headers);
    } catch (_) {
      throw FacultyApiException(
        'Network error while loading KRA configuration.',
        errorCode: 'network',
      );
    }
    final body = await _decodeJson(response);
    if (response.statusCode != 200) {
      throw FacultyApiException(
        body['message'] as String? ?? 'Unable to load KRA configuration.',
        statusCode: response.statusCode,
      );
    }
    _kraCache = KraConfigurationBundle.fromJson(body);
    return _kraCache!;
  }

  /// KRA I Criterion A (SET/SEF scope) from server configuration.
  static Future<KraCriterionTarget> getKraICriterionA() async {
    final bundle = await getKraConfiguration();
    final target = bundle.kraICriterionA;
    if (target == null) {
      throw FacultyApiException(
        'KRA I Criterion A is not configured on the server.',
        errorCode: 'configuration',
      );
    }
    return target;
  }

  static Future<List<FacultyDocument>> listDocuments() async {
    if (useMockDocuments) {
      await _delay();
      return FacultyMockData.documents;
    }
    final config = await getKraConfiguration();
    final headers = await _authHeaders();
    http.Response response;
    try {
      response = await http.get(_uri('/api/v1/faculty/documents'), headers: headers);
    } catch (_) {
      throw FacultyApiException(
        'Network error while loading documents.',
        errorCode: 'network',
      );
    }
    final body = await _decodeJson(response);
    if (response.statusCode != 200) {
      throw FacultyApiException(
        body['message'] as String? ?? 'Unable to load documents.',
        statusCode: response.statusCode,
        errorCode: body['error'] as String?,
      );
    }
    final rows = body['documents'] as List<dynamic>? ?? [];
    return rows
        .map(
          (d) => FacultyDocumentParser.fromListJson(
            d as Map<String, dynamic>,
            config,
          ),
        )
        .toList();
  }

  static Future<DocumentDetail> getDocumentDetail(String id) async {
    if (useMockDocuments) {
      await _delay();
      return FacultyMockData.detailFor(id);
    }
    final config = await getKraConfiguration();
    final headers = await _authHeaders();
    http.Response response;
    try {
      response = await http.get(
        _uri('/api/v1/faculty/documents/$id'),
        headers: headers,
      );
    } catch (_) {
      throw FacultyApiException(
        'Network error while loading document details.',
        errorCode: 'network',
      );
    }
    final body = await _decodeJson(response);
    if (response.statusCode == 404) {
      throw FacultyApiException(
        body['message'] as String? ?? 'Document not found.',
        statusCode: 404,
        errorCode: 'not_found',
      );
    }
    if (response.statusCode != 200) {
      throw FacultyApiException(
        body['message'] as String? ?? 'Unable to load document.',
        statusCode: response.statusCode,
        errorCode: body['error'] as String?,
      );
    }
    final doc = body['document'] as Map<String, dynamic>;
    return FacultyDocumentParser.fromDetailJson(doc, config);
  }

  static Future<DocumentDetail> uploadDocument({
    required int periodId,
    required int criterionId,
    required String title,
    required String fileName,
    required Uint8List bytes,
    required String mimeType,
  }) async {
    if (useMockDocuments) {
      throw FacultyApiException('Mock document upload is disabled for integration.');
    }
    final token = await _bearer();
    if (token == null || token.isEmpty) {
      throw FacultyApiException('Sign in to upload documents.', errorCode: 'auth');
    }

    final request = http.MultipartRequest('POST', _uri('/api/v1/faculty/documents'));
    request.headers['Accept'] = 'application/json';
    request.headers['Authorization'] = 'Bearer $token';
    request.fields['period_id'] = '$periodId';
    request.fields['criterion_id'] = '$criterionId';
    request.fields['title'] = title;
    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: fileName,
        contentType: MediaType.parse(mimeType),
      ),
    );

    http.StreamedResponse streamed;
    try {
      streamed = await request.send();
    } catch (_) {
      throw FacultyApiException(
        'Network error during upload.',
        errorCode: 'network',
      );
    }

    final response = await http.Response.fromStream(streamed);
    final body = await _decodeJson(response);

    if (response.statusCode == 409) {
      throw FacultyApiException(
        body['message'] as String? ??
            'This file was already submitted and is still active.',
        statusCode: 409,
        errorCode: body['error'] as String? ?? 'duplicate_evidence',
      );
    }
    if (response.statusCode == 403) {
      throw FacultyApiException(
        body['message'] as String? ?? 'Submissions are closed for this period.',
        statusCode: 403,
        errorCode: body['error'] as String? ?? 'submission_closed',
      );
    }
    if (response.statusCode == 413) {
      throw FacultyApiException(
        body['message'] as String? ?? 'File exceeds maximum upload size.',
        statusCode: 413,
        errorCode: 'validation',
      );
    }
    if (response.statusCode != 201) {
      throw FacultyApiException(
        body['message'] as String? ?? 'Upload failed.',
        statusCode: response.statusCode,
        errorCode: body['error'] as String?,
      );
    }

    final docId = (body['document'] as Map<String, dynamic>)['documentId'];
    return getDocumentDetail('$docId');
  }

  static String mimeTypeForExtension(String? extension) {
    switch (extension?.toLowerCase()) {
      case 'pdf':
        return 'application/pdf';
      case 'png':
        return 'image/png';
      case 'jpg':
      case 'jpeg':
        return 'image/jpeg';
      default:
        return 'application/octet-stream';
    }
  }

  static Future<List<EvaluationPeriod>> _loadBundledPeriods() async {
    final text = await rootBundle.loadString(
      'admin_reviewer_web/assets/data/evaluation-periods.json',
    );
    final data = jsonDecode(text) as Map<String, dynamic>;
    if (data['timezone'] != 'Asia/Manila') {
      throw const FormatException('Unsupported evaluation timezone.');
    }
    return (data['periods'] as List)
        .map((p) => EvaluationPeriod.fromJson(p as Map<String, dynamic>))
        .toList();
  }

  static Future<FacultyProfile> getProfile() async {
    await _delay();
    return FacultyMockData.profile;
  }

  static Future<DashboardSummary> getDashboardSummary() async {
    await _delay();
    return FacultyMockData.dashboardSummary;
  }

  static Future<List<KraOverviewItem>> getKraOverview() async {
    await _delay();
    return FacultyMockData.kraOverview;
  }

  static Future<List<ActivityItem>> getRecentActivity() async {
    await _delay();
    return FacultyMockData.recentActivity;
  }

  static Future<List<AppNotification>> listNotifications() async {
    await _delay();
    return FacultyMockData.notifications;
  }

  static Future<RankSimulationView> getRankSimulation() async {
    await _delay();
    return FacultyMockData.rankSimulation;
  }

  static Future<List<KraSectionMock>> getKraAssessment() async {
    await _delay();
    return FacultyMockData.kraSections;
  }

  static Future<void> changePassword() async {
    throw UnimplementedError('Flask auth API not connected');
  }

  static Future<void> _delay() =>
      Future<void>.delayed(const Duration(milliseconds: 200));
}
