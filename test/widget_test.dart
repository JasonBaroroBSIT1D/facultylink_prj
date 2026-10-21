import 'package:flutter_test/flutter_test.dart';
import 'package:facultylink_prj/app.dart';

void main() {
  testWidgets('Welcome screen shows FacultyLink branding', (WidgetTester tester) async {
    await tester.pumpWidget(const FacultyLinkApp());
    await tester.pumpAndSettle();

    expect(find.textContaining('Your Academic Growth'), findsOneWidget);
    expect(find.text('Get Started'), findsOneWidget);
    expect(find.text('Sign In'), findsOneWidget);
  });
}
