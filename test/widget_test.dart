import 'package:flutter_test/flutter_test.dart';
import 'package:facultylink_prj/app.dart';
import 'package:facultylink_prj/core/constants/app_disclaimers.dart';

void main() {
  testWidgets('Welcome screen shows FacultyLink branding', (WidgetTester tester) async {
    await tester.pumpWidget(const FacultyLinkApp());
    await tester.pumpAndSettle();

    expect(find.text(AppDisclaimers.systemName), findsOneWidget);
    expect(find.text('Organize evidence. Review KRA assessment progress.'), findsOneWidget);
    expect(find.text('Get Started'), findsOneWidget);
  });
}
