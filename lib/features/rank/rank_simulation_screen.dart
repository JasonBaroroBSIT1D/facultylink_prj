import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';
import '../../services/api/faculty_api.dart';
import '../../core/constants/app_disclaimers.dart';

class RankSimulationScreen extends StatefulWidget {
  const RankSimulationScreen({super.key});

  @override
  State<RankSimulationScreen> createState() => _RankSimulationScreenState();
}

class _RankSimulationScreenState extends State<RankSimulationScreen> {
  RankSimulationView? _view;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    FacultyApi.getRankSimulation().then((v) {
      if (!mounted) return;
      setState(() {
        _view = v;
        _loading = false;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgLight,
      appBar: AppBar(
        title: const Text('Rank Simulation'),
        backgroundColor: AppColors.white,
        foregroundColor: AppColors.deepNavy,
        elevation: 0,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(
                    'Sample Data',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: AppColors.textMuted,
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(AppDisclaimers.rankSimulation, style: Theme.of(context).textTheme.bodySmall),
                      const SizedBox(height: 12),
                      _row('Current rank', _view!.currentRank),
                      _row('Assessment period', _view!.assessmentPeriod),
                      _row('Status', _view!.assessmentStatus),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                Text('KRA score breakdown', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                ..._view!.kraScores.map(
                  (e) => Card(
                    child: ListTile(
                      title: Text(e.key),
                      trailing: Text(e.value, style: const TextStyle(fontWeight: FontWeight.w700)),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text('Simulation summary', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _row('Total eligible points', _view!.totalEligiblePoints),
                        _row('Simulated rank', _view!.simulatedRank),
                        _row('Readiness', _view!.readinessStatus),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text('Missing requirements', style: Theme.of(context).textTheme.titleSmall),
                ..._view!.missingRequirements.map((m) => ListTile(dense: true, leading: const Icon(Icons.info_outline, color: AppColors.cyan), title: Text(m))),
              ],
            ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(child: Text(label, style: const TextStyle(color: AppColors.textMuted))),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
