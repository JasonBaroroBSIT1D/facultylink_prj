/// FacultyLink Flask API base URL (development).
abstract final class ApiConfig {
  /// Override with `--dart-define=FL_API_BASE=http://10.0.2.2:5000` for Android emulator.
  static const baseUrl = String.fromEnvironment(
    'FL_API_BASE',
    defaultValue: 'http://127.0.0.1:5000',
  );
}
