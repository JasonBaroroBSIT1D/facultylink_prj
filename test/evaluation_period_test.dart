import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:facultylink_prj/models/evaluation_period.dart';
import 'package:facultylink_prj/services/api/faculty_api.dart';
import 'package:facultylink_prj/services/evaluation_period_controller.dart';
import 'package:facultylink_prj/widgets/fl_evaluation_period_card.dart';
import 'package:facultylink_prj/features/documents/upload_document_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final data =
      jsonDecode(
            File(
              'admin_reviewer_web/assets/data/evaluation-periods.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
  final periods = (data['periods'] as List)
      .map((p) => EvaluationPeriod.fromJson(p as Map<String, dynamic>))
      .toList();
  final november = periods.last;

  test(
    'Manila boundaries, formatting and access match the shared web contract',
    () {
      expect(
        november.statusAt(DateTime.parse('2026-10-31T23:59:59Z')),
        EvaluationPeriodStatus.upcoming,
      );
      expect(
        november.statusAt(DateTime.parse('2026-11-01T00:00:00Z')),
        EvaluationPeriodStatus.open,
      );
      expect(
        november.statusAt(DateTime.parse('2026-11-30T15:59:00Z')),
        EvaluationPeriodStatus.closed,
      );
      expect(
        november.submissionsAllowedAt(DateTime.parse('2026-11-01T00:00:00Z')),
        isTrue,
      );
      expect(
        november.reviewsAllowedAt(DateTime.parse('2026-11-30T15:59:00Z')),
        isFalse,
      );
      expect(
        EvaluationPeriod.formatManila(november.opensAt),
        'Nov 1, 2026 • 8:00 AM',
      );
      expect(
        EvaluationPeriod.formatManila(november.closesAt),
        'Nov 30, 2026 • 11:59 PM',
      );
      expect(
        EvaluationPeriod.current(
          periods,
          DateTime.parse('2026-10-22T00:00:00Z'),
        )?.id,
        'EP-2026-10',
      );
      expect(EvaluationPeriod.current([], DateTime.now()), isNull);
      final invalid = Map<String, dynamic>.from(
        (data['periods'] as List).last as Map,
      );
      invalid['closesAt'] = invalid['opensAt'];
      expect(() => EvaluationPeriod.fromJson(invalid), throwsFormatException);
      invalid['opensAt'] = '2026-02-30T08:00:00+08:00';
      expect(() => EvaluationPeriod.fromJson(invalid), throwsFormatException);
    },
  );

  test('Flutter bundles the same canonical seed used by the web', () async {
    FacultyApi.useBundledEvaluationPeriods = true;
    addTearDown(() => FacultyApi.useBundledEvaluationPeriods = false);
    final bundled = await FacultyApi.getEvaluationPeriods();
    expect(bundled.map((p) => p.id), periods.map((p) => p.id));
    expect(bundled.last.opensAt, november.opensAt);
  });

  for (final state in [
    ('2026-10-31T23:59:00Z', 'Upcoming', false),
    ('2026-11-01T00:00:00Z', 'Open', true),
    ('2026-11-30T15:59:00Z', 'Closed', false),
  ]) {
    testWidgets(
      'compact mobile card: ${state.$2}, narrow viewport and larger text',
      (tester) async {
        tester.view.physicalSize = const Size(320, 850);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        final controller = EvaluationPeriodController(
          loader: () async => [november],
          clock: () => DateTime.parse(state.$1),
          live: false,
        );
        await controller.load();
        var submissions = 0;
        await tester.pumpWidget(
          MaterialApp(
            home: MediaQuery(
              data: const MediaQueryData(textScaler: TextScaler.linear(1.3)),
              child: Scaffold(
                body: SingleChildScrollView(
                  child: FlEvaluationPeriodCard(
                    controller: controller,
                    onSubmit: () => submissions++,
                  ),
                ),
              ),
            ),
          ),
        );
        await tester.pumpAndSettle();
        expect(find.text(state.$2), findsOneWidget);
        expect(find.text('Nov 1, 2026 • 8:00 AM'), findsOneWidget);
        expect(find.text('Nov 30, 2026 • 11:59 PM'), findsOneWidget);
        expect(
          find.text('Submit Documents'),
          state.$3 ? findsOneWidget : findsNothing,
        );
        if (state.$3) {
          await tester.tap(find.text('Submit Documents'));
          expect(submissions, 1);
        }
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox.shrink());
        controller.dispose();
      },
    );
  }

  testWidgets(
    'the submission action updates when an open period reaches its deadline',
    (tester) async {
      var now = november.closesAt.subtract(const Duration(seconds: 1));
      final controller = EvaluationPeriodController(
        loader: () async => [november],
        clock: () => now,
        live: false,
      );
      await controller.load();
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FlEvaluationPeriodCard(
              controller: controller,
              onSubmit: () {},
            ),
          ),
        ),
      );
      expect(find.text('Submit Documents'), findsOneWidget);
      now = november.closesAt;
      controller.syncToClock();
      await tester.pump();
      expect(find.text('Closed'), findsOneWidget);
      expect(find.text('Submit Documents'), findsNothing);
      await tester.pumpWidget(const SizedBox.shrink());
      controller.dispose();
    },
  );

  testWidgets('paused, empty and error states never expose a submission action', (
    tester,
  ) async {
    final pausedJson = Map<String, dynamic>.from(
      (data['periods'] as List).last as Map,
    )..['submissionEnabled'] = false;
    final paused = EvaluationPeriod.fromJson(pausedJson);
    final controller = EvaluationPeriodController(
      loader: () async => [paused],
      clock: () => DateTime.parse('2026-11-02T00:00:00Z'),
      live: false,
    );
    await controller.load();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: FlEvaluationPeriodCard(controller: controller, onSubmit: () {}),
        ),
      ),
    );
    expect(
      find.text('Submissions are paused for this period.'),
      findsOneWidget,
    );
    expect(find.text('Submit Documents'), findsNothing);
    await tester.pumpWidget(const SizedBox.shrink());
    controller.dispose();
    for (final fail in [false, true]) {
      final empty = EvaluationPeriodController(
        loader: () async {
          if (fail) throw Exception('offline');
          return [];
        },
        live: false,
      );
      await empty.load();
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FlEvaluationPeriodCard(controller: empty, onSubmit: () {}),
          ),
        ),
      );
      expect(find.text('Submit Documents'), findsNothing);
      expect(empty.canSubmit, isFalse);
      expect(
        find.text(
          fail
              ? 'Try again'
              : 'No evaluation period is configured. Submissions are unavailable.',
        ),
        findsOneWidget,
      );
      await tester.pumpWidget(const SizedBox.shrink());
      empty.dispose();
    }
  });

  testWidgets(
    'upload disables submission for a closed period even through a direct route',
    (tester) async {
      final controller = EvaluationPeriodController(
        loader: () async => periods,
        clock: () => DateTime.parse('2026-10-22T00:00:00Z'),
        live: false,
      );
      await controller.load();
      controller.select('EP-2026-09');
      await tester.pumpWidget(
        MaterialApp(
          home: UploadDocumentScreen(periodController: controller),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      expect(find.text('Closed'), findsOneWidget);
      expect(find.text('Submissions unavailable'), findsOneWidget);
      expect(controller.canSubmit, isFalse);
      await tester.pumpWidget(const SizedBox.shrink());
      controller.dispose();
    },
  );
}
