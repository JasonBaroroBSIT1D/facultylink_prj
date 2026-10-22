import 'package:flutter/material.dart';
import '../../core/kra/kra_structure.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';
import '../../services/api/faculty_api.dart';
import '../../widgets/fl_evaluation_period_card.dart';
import 'kra_indicator_detail_screen.dart';

class KraAssessmentScreen extends StatefulWidget {
  const KraAssessmentScreen({super.key});

  @override
  State<KraAssessmentScreen> createState() => _KraAssessmentScreenState();
}

class _KraAssessmentScreenState extends State<KraAssessmentScreen> {
  List<KraSectionMock> _sections = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    FacultyApi.getKraAssessment().then((s) {
      if (!mounted) return;
      setState(() {
        _sections = s;
        _loading = false;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgLight,
      appBar: AppBar(title: const Text('KRA Assessment')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
              children: [
                const Padding(
                  padding: EdgeInsets.only(top: 12, bottom: 8),
                  child: FlEvaluationPeriodCard(),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(4, 12, 4, 8),
                  child: Text(
                    'KRA → Criterion → Indicator → documents',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textMuted),
                  ),
                ),
                ..._sections.map((section) => _KraSectionCard(section: section)),
              ],
            ),
    );
  }
}

class _KraSectionCard extends StatelessWidget {
  const _KraSectionCard({required this.section});

  final KraSectionMock section;

  @override
  Widget build(BuildContext context) {
    final kraKey = KraStructure.kraOptions.firstWhere(
      (k) => section.title.startsWith(k),
      orElse: () => section.title,
    );
    final expected = KraStructure.lettersFor(kraKey);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          childrenPadding: const EdgeInsets.fromLTRB(8, 0, 8, 12),
          title: Text(section.title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
          subtitle: Text(
            '${section.criteria.length} of ${expected.length} criteria',
            style: TextStyle(color: AppColors.textMuted, fontSize: 12),
          ),
          children: section.criteria
              .map((c) => _CriterionTile(kraTitle: section.title, criterion: c))
              .toList(),
        ),
      ),
    );
  }
}

class _CriterionTile extends StatelessWidget {
  const _CriterionTile({required this.kraTitle, required this.criterion});

  final String kraTitle;
  final KraCriterionMock criterion;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: AppColors.bgLight,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(horizontal: 12),
        title: Text(
          'Criterion ${criterion.code}',
          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
        ),
        subtitle: Text(criterion.title, style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
        children: criterion.indicators
            .map(
              (ind) => ListTile(
                dense: true,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
                title: Text('${ind.code} — ${ind.title}', style: const TextStyle(fontSize: 13)),
                subtitle: Text('Score: ${ind.aggregatedScore}', style: const TextStyle(fontSize: 11)),
                trailing: Icon(Icons.chevron_right, size: 20, color: AppColors.textMuted),
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute<void>(
                    builder: (_) => KraIndicatorDetailScreen(
                      kraTitle: kraTitle,
                      criterion: criterion,
                      indicator: ind,
                    ),
                  ),
                ),
              ),
            )
            .toList(),
      ),
    );
  }
}
