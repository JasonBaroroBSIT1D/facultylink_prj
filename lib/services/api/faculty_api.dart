import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import '../../core/config/api_config.dart';
import '../../models/evaluation_period.dart';
import '../../models/faculty_models.dart';
import '../auth/auth_session.dart';
import '../mock/faculty_mock_data.dart';

/// Faculty mobile API — evaluation periods use Flask when authenticated.
abstract final class FacultyApi {
  /// Legacy mock flag for non-evaluation endpoints.
  static bool useMock = true;

  /// When true, load bundled JSON for evaluation periods (tests / offline dev only).
  static bool useBundledEvaluationPeriods = false;

  static Uri _uri(String path) => Uri.parse('${ApiConfig.baseUrl}$path');

  static Future<List<EvaluationPeriod>> getEvaluationPeriods() async {
    if (useBundledEvaluationPeriods) {
      return _loadBundledPeriods();
    }

    final token = await AuthSession.instance.readToken();
    if (token == null || token.isEmpty) {
      throw const FormatException(
        'Sign in to load evaluation periods from the server.',
      );
    }

    final response = await http.get(
      _uri('/api/v1/evaluation-periods'),
      headers: {
        'Accept': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    Map<String, dynamic> body;
    try {
      body = jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      throw const FormatException('Unable to load evaluation periods.');
    }

    if (response.statusCode != 200) {
      throw FormatException(
        body['message'] as String? ?? 'Unable to load evaluation periods.',
      );
    }

    final rows = body['periods'] as List<dynamic>? ?? [];
    return rows
        .map((p) => EvaluationPeriod.fromJson(p as Map<String, dynamic>))
        .toList();
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

  static Future<List<FacultyDocument>> listDocuments() async {
    await _delay();
    return FacultyMockData.documents;
  }

  static Future<DocumentDetail> getDocumentDetail(String id) async {
    await _delay();
    return FacultyMockData.detailFor(id);
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

  static Future<void> submitDocument() async {
    throw UnimplementedError('Flask upload API not connected');
  }

  static Future<void> changePassword() async {
    throw UnimplementedError('Flask auth API not connected');
  }

  static Future<void> _delay() =>
      Future<void>.delayed(const Duration(milliseconds: 200));
}
