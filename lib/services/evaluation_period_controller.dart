import 'dart:async';
import 'package:flutter/widgets.dart';
import '../models/evaluation_period.dart';
import 'api/faculty_api.dart';

/// Shared mobile demo state. It does not read another browser's localStorage.
class EvaluationPeriodController extends ChangeNotifier
    with WidgetsBindingObserver {
  EvaluationPeriodController({
    Future<List<EvaluationPeriod>> Function()? loader,
    DateTime Function()? clock,
    this.live = true,
  }) : _loader = loader ?? FacultyApi.getEvaluationPeriods,
       _clock = clock ?? DateTime.now;

  static final instance = EvaluationPeriodController();
  final Future<List<EvaluationPeriod>> Function() _loader;
  final DateTime Function() _clock;
  final bool live;
  List<EvaluationPeriod> periods = [];
  bool loading = true;
  String? error;
  String? _selectedId;
  Future<void>? _pending;
  Timer? _timer;
  bool _observing = false;
  bool _disposed = false;

  DateTime get now => _clock();
  EvaluationPeriod? get current =>
      periods.where((p) => p.id == _selectedId).firstOrNull ??
      EvaluationPeriod.current(periods, now);
  bool get canSubmit =>
      !loading &&
      error == null &&
      (current?.submissionsAllowedAt(now) ?? false);

  /// Loads periods once unless [force] is true (e.g. screen refresh after login).
  Future<void> load({bool force = false}) {
    if (force) _pending = null;
    if (!force && _pending != null) return _pending!;
    if (!force && !loading && periods.isNotEmpty && error == null) {
      return Future.value();
    }
    return _pending ??= _load();
  }

  Future<void> refresh() => load(force: true);

  /// Rebuild UI when using an injected [clock] (widget tests).
  void syncToClock() => notifyListeners();

  Future<void> _load() async {
    loading = true;
    error = null;
    try {
      final data = await _loader();
      if (_disposed) return;
      periods = data;
    } catch (_) {
      if (_disposed) return;
      error =
          'Evaluation periods could not be loaded. Submissions are unavailable.';
    }
    loading = false;
    _pending = null;
    if (live && !_observing) {
      WidgetsBinding.instance.addObserver(this);
      _observing = true;
    }
    notifyListeners();
    _schedule();
  }

  void select(String? id) {
    _selectedId = id;
    notifyListeners();
  }

  void _schedule() {
    _timer?.cancel();
    if (!live || _disposed) return;
    var delay = 30000;
    for (final period in periods) {
      for (final boundary in [period.opensAt, period.closesAt]) {
        final delta = boundary.difference(now).inMilliseconds;
        if (delta > 0 && delta + 20 < delay) delay = delta + 20;
      }
    }
    _timer = Timer(Duration(milliseconds: delay), () {
      notifyListeners();
      _schedule();
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      notifyListeners();
      _schedule();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    _timer?.cancel();
    if (_observing) WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }
}
