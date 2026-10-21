import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';
import '../../services/api/faculty_api.dart';
import '../../widgets/fl_mock_banner.dart';
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
      appBar: AppBar(
        title: const Text('KRA Assessment'),
        backgroundColor: AppColors.white,
        foregroundColor: AppColors.deepNavy,
        elevation: 0,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.only(bottom: 24),
              children: [
                const FlMockBanner(),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    'KRA → Criterion → Indicator → documents → validation → eligible points',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textMuted),
                  ),
                ),
                ..._sections.map((section) => _KraSectionTile(section: section)),
              ],
            ),
    );
  }
}

class _KraSectionTile extends StatelessWidget {
  const _KraSectionTile({required this.section});

  final KraSectionMock section;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ExpansionTile(
        title: Text(section.title, style: const TextStyle(fontWeight: FontWeight.w700)),
        children: section.criteria
            .map(
              (c) => ExpansionTile(
                title: Text('Criterion ${c.code}: ${c.title}', style: const TextStyle(fontSize: 14)),
                children: c.indicators
                    .map(
                      (ind) => ListTile(
                        title: Text('${ind.code} — ${ind.title}'),
                        subtitle: Text('Score: ${ind.aggregatedScore}'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute<void>(
                            builder: (_) => KraIndicatorDetailScreen(
                              kraTitle: section.title,
                              criterion: c,
                              indicator: ind,
                            ),
                          ),
                        ),
                      ),
                    )
                    .toList(),
              ),
            )
            .toList(),
      ),
    );
  }
}
