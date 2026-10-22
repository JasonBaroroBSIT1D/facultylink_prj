enum EvaluationPeriodStatus { upcoming, open, closed }

/// Same schema and [opening, closing) access window as the web demonstration.
class EvaluationPeriod {
  const EvaluationPeriod({
    required this.id,
    required this.name,
    required this.academicYear,
    required this.semester,
    required this.opensAt,
    required this.closesAt,
    required this.description,
    required this.submissionEnabled,
    required this.reviewEnabled,
  });

  factory EvaluationPeriod.fromJson(Map<String, dynamic> json) {
    DateTime parse(String field) {
      final raw = json[field] as String;
      if (!RegExp(
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$',
      ).hasMatch(raw)) {
        throw const FormatException(
          'Evaluation periods require Asia/Manila times.',
        );
      }
      final date = DateTime.parse(raw).toUtc();
      if (date
              .add(const Duration(hours: 8))
              .toIso8601String()
              .substring(0, 19) !=
          raw.substring(0, 19)) {
        throw const FormatException('Invalid evaluation period date.');
      }
      return date;
    }

    final opens = parse('opensAt');
    final closes = parse('closesAt');
    if (!closes.isAfter(opens)) {
      throw const FormatException('Closing must follow opening.');
    }
    return EvaluationPeriod(
      id: json['id'] as String,
      name: json['name'] as String,
      academicYear: json['academicYear'] as String,
      semester: json['semester'] as String,
      opensAt: opens,
      closesAt: closes,
      description: json['description'] as String,
      submissionEnabled: json['submissionEnabled'] as bool,
      reviewEnabled: json['reviewEnabled'] as bool,
    );
  }

  final String id, name, academicYear, semester, description;
  final DateTime opensAt, closesAt;
  final bool submissionEnabled, reviewEnabled;

  EvaluationPeriodStatus statusAt(DateTime now) {
    if (now.isBefore(opensAt)) return EvaluationPeriodStatus.upcoming;
    if (!now.isBefore(closesAt)) return EvaluationPeriodStatus.closed;
    return EvaluationPeriodStatus.open;
  }

  bool submissionsAllowedAt(DateTime now) =>
      statusAt(now) == EvaluationPeriodStatus.open && submissionEnabled;
  bool reviewsAllowedAt(DateTime now) =>
      statusAt(now) == EvaluationPeriodStatus.open && reviewEnabled;

  String remainingAt(DateTime now) {
    final state = statusAt(now);
    if (state == EvaluationPeriodStatus.closed) {
      return 'The submission window has ended.';
    }
    final minutes =
        ((state == EvaluationPeriodStatus.open ? closesAt : opensAt)
                    .difference(now)
                    .inMilliseconds /
                60000)
            .ceil();
    final days = minutes ~/ 1440;
    final hours = (minutes % 1440) ~/ 60;
    final text = days > 0
        ? '${days}d ${hours}h'
        : hours > 0
        ? '${hours}h ${minutes % 60}m'
        : '${minutes < 1 ? 1 : minutes}m';
    return state == EvaluationPeriodStatus.open
        ? '$text remaining'
        : 'Opens in $text';
  }

  static String formatManila(DateTime date) {
    final wall = date.toUtc().add(const Duration(hours: 8));
    const months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    final hour = wall.hour % 12 == 0 ? 12 : wall.hour % 12;
    return '${months[wall.month - 1]} ${wall.day}, ${wall.year} • $hour:${wall.minute.toString().padLeft(2, '0')} ${wall.hour < 12 ? 'AM' : 'PM'}';
  }

  static EvaluationPeriod? current(
    List<EvaluationPeriod> periods,
    DateTime now,
  ) {
    final open =
        periods
            .where((p) => p.statusAt(now) == EvaluationPeriodStatus.open)
            .toList()
          ..sort((a, b) => a.closesAt.compareTo(b.closesAt));
    final upcoming =
        periods
            .where((p) => p.statusAt(now) == EvaluationPeriodStatus.upcoming)
            .toList()
          ..sort((a, b) => a.opensAt.compareTo(b.opensAt));
    final closed =
        periods
            .where((p) => p.statusAt(now) == EvaluationPeriodStatus.closed)
            .toList()
          ..sort((a, b) => b.closesAt.compareTo(a.closesAt));
    return open.firstOrNull ?? upcoming.firstOrNull ?? closed.firstOrNull;
  }
}
