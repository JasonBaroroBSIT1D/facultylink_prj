import '../../models/faculty_models.dart';
import '../mock/faculty_mock_data.dart';

/// Faculty mobile API — swap implementations when Flask backend is ready.
abstract final class FacultyApi {
  static bool useMock = true;

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

  static Future<void> _delay() => Future<void>.delayed(const Duration(milliseconds: 200));
}
