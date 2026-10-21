import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../services/mock/faculty_mock_data.dart';

class FlMockBanner extends StatelessWidget {
  const FlMockBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      color: AppColors.brightBlue.withValues(alpha: 0.1),
      child: Text(
        FacultyMockData.mockBanner,
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(color: AppColors.textMuted),
      ),
    );
  }
}
