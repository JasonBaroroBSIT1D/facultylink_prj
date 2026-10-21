import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';

class ValidationResultsScreen extends StatelessWidget {
  const ValidationResultsScreen({super.key, required this.detail});

  final DocumentDetail detail;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Rule-Based Validation')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.bgLight,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.cyan),
            ),
            child: Text(detail.validationSummary),
          ),
          const SizedBox(height: 16),
          ...detail.validationChecks.map(
            (c) => Card(
              child: ListTile(
                leading: Icon(
                  c.passed ? Icons.check_circle : Icons.warning_amber_rounded,
                  color: c.passed ? Colors.green : Colors.orange,
                ),
                title: Text(c.name),
                subtitle: Text(c.explanation),
              ),
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Authoritative validation comes from the shared Flask Rule-Based Engine — Flutter does not approve documents independently.',
            style: TextStyle(fontSize: 12, color: AppColors.textMuted),
          ),
        ],
      ),
    );
  }
}
