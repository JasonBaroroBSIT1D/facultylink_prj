class FacultyApiException implements Exception {
  FacultyApiException(this.message, {this.errorCode, this.statusCode});

  final String message;
  final String? errorCode;
  final int? statusCode;

  bool get isDuplicate => errorCode == 'duplicate_evidence';
  bool get isClosedPeriod =>
      errorCode == 'submission_closed' || statusCode == 403;
  bool get isNetwork =>
      errorCode == 'network' || statusCode == null;

  @override
  String toString() => message;
}
