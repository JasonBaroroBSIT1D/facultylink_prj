import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';

/// Original faculty-themed illustration (not copied from reference artwork).
class WelcomeIllustration extends StatelessWidget {
  const WelcomeIllustration({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 200,
      width: double.infinity,
      child: CustomPaint(
        painter: _WelcomeIllustrationPainter(),
        child: const SizedBox.expand(),
      ),
    );
  }
}

class _WelcomeIllustrationPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    final building = Paint()..color = AppColors.academicBlue.withValues(alpha: 0.15);
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(w * 0.08, h * 0.35, w * 0.84, h * 0.55), const Radius.circular(12)),
      building,
    );

    final columnPaint = Paint()..color = AppColors.brightBlue.withValues(alpha: 0.35);
    for (var i = 0; i < 5; i++) {
      final x = w * 0.14 + i * (w * 0.16);
      canvas.drawRRect(
        RRect.fromRectAndRadius(Rect.fromLTWH(x, h * 0.42, w * 0.06, h * 0.38), const Radius.circular(4)),
        columnPaint,
      );
    }

    final roof = Paint()..color = AppColors.deepNavy.withValues(alpha: 0.2);
    final roofPath = Path()
      ..moveTo(w * 0.04, h * 0.38)
      ..lineTo(w * 0.5, h * 0.12)
      ..lineTo(w * 0.96, h * 0.38)
      ..close();
    canvas.drawPath(roofPath, roof);

    final person = Paint()..color = AppColors.academicBlue;
    canvas.drawCircle(Offset(w * 0.72, h * 0.52), w * 0.045, person);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(w * 0.72, h * 0.68), width: w * 0.12, height: h * 0.22),
        const Radius.circular(20),
      ),
      person,
    );

    final doc = Paint()..color = AppColors.cyan.withValues(alpha: 0.85);
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(w * 0.22, h * 0.48, w * 0.22, h * 0.28), const Radius.circular(8)),
      doc,
    );

    final line = Paint()
      ..color = AppColors.white.withValues(alpha: 0.9)
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;
    for (var i = 0; i < 3; i++) {
      canvas.drawLine(
        Offset(w * 0.26, h * 0.56 + i * 14),
        Offset(w * 0.38, h * 0.56 + i * 14),
        line,
      );
    }

    final cap = Paint()..color = AppColors.cyan;
    final capPath = Path()
      ..moveTo(w * 0.68, h * 0.46)
      ..lineTo(w * 0.78, h * 0.5)
      ..lineTo(w * 0.88, h * 0.46)
      ..lineTo(w * 0.78, h * 0.42)
      ..close();
    canvas.drawPath(capPath, cap);
    canvas.drawRect(Rect.fromLTWH(w * 0.74, h * 0.5, w * 0.08, h * 0.02), cap);

    final tassel = Paint()
      ..color = AppColors.brightBlue
      ..strokeWidth = 2;
    canvas.drawLine(Offset(w * 0.86, h * 0.47), Offset(w * 0.9, h * 0.54), tassel);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
