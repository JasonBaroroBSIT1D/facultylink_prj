import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';

class KraIndicatorDetailScreen extends StatelessWidget {
  const KraIndicatorDetailScreen({
    super.key,
    required this.kraTitle,
    required this.criterion,
    required this.indicator,
  });

  final String kraTitle;
  final KraCriterionMock criterion;
  final KraIndicatorMock indicator;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(indicator.code)),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(kraTitle, style: const TextStyle(color: AppColors.textMuted, fontSize: 13)),
          Text(
            'Criterion ${criterion.code}: ${criterion.title}',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          Text(indicator.title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 16),
          _InfoRow(label: 'Aggregated score (backend)', value: indicator.aggregatedScore),
          _InfoRow(label: 'Eligible points', value: 'Awaiting backend evaluation'),
          const SizedBox(height: 16),
          if (indicator.semesters.isNotEmpty) ...[
            Text('Evaluation periods (mock)', style: Theme.of(context).textTheme.titleSmall),
            ...indicator.semesters.map((s) => ListTile(dense: true, leading: const Icon(Icons.calendar_today, size: 18), title: Text(s))),
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Text(
                'Supports separate semester files or consolidated multi-semester documents. Duplicate semester warnings from backend when integrated.',
                style: TextStyle(fontSize: 12, color: AppColors.textMuted),
              ),
            ),
          ],
          const SizedBox(height: 16),
          Text('Required evidence', style: Theme.of(context).textTheme.titleSmall),
          ...indicator.evidence.map((e) => ListTile(dense: true, leading: const Icon(Icons.checklist, size: 18), title: Text(e))),
          const SizedBox(height: 16),
          Text('Submitted documents', style: Theme.of(context).textTheme.titleSmall),
          const ListTile(
            dense: true,
            title: Text('Linked from My Documents when API connects'),
            subtitle: Text('Validation status shown per document'),
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: Text(label, style: const TextStyle(color: AppColors.textMuted))),
          Expanded(child: Text(value, textAlign: TextAlign.end, style: const TextStyle(fontWeight: FontWeight.w600))),
        ],
      ),
    );
  }
}
