import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';
import '../../services/api/faculty_api.dart';
import '../../widgets/fl_mock_banner.dart';
import '../../widgets/fl_summary_card.dart';
import '../documents/upload_document_screen.dart';
import '../notifications/notifications_screen.dart';

class FacultyDashboardScreen extends StatefulWidget {
  const FacultyDashboardScreen({super.key, required this.onNavigateTab});

  final void Function(int tabIndex) onNavigateTab;

  @override
  State<FacultyDashboardScreen> createState() => _FacultyDashboardScreenState();
}

class _FacultyDashboardScreenState extends State<FacultyDashboardScreen> {
  FacultyProfile? _profile;
  DashboardSummary? _summary;
  List<KraOverviewItem> _kras = [];
  List<ActivityItem> _activity = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final results = await Future.wait([
      FacultyApi.getProfile(),
      FacultyApi.getDashboardSummary(),
      FacultyApi.getKraOverview(),
      FacultyApi.getRecentActivity(),
    ]);
    if (!mounted) return;
    setState(() {
      _profile = results[0] as FacultyProfile;
      _summary = results[1] as DashboardSummary;
      _kras = results[2] as List<KraOverviewItem>;
      _activity = results[3] as List<ActivityItem>;
      _loading = false;
    });
  }

  String _greeting() {
    final h = DateTime.now().hour;
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgLight,
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : CustomScrollView(
                slivers: [
                  const SliverToBoxAdapter(child: FlMockBanner()),
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(20, 16, 12, 8),
                      child: Row(
                        children: [
                          CircleAvatar(
                            radius: 26,
                            backgroundColor: AppColors.academicBlue,
                            child: Text(
                              _profile!.fullName.split(' ').map((e) => e[0]).take(2).join(),
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(_greeting(), style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
                                Text(
                                  _profile!.fullName,
                                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                        fontWeight: FontWeight.w800,
                                        color: AppColors.deepNavy,
                                      ),
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            onPressed: () => Navigator.push(
                              context,
                              MaterialPageRoute<void>(builder: (_) => const NotificationsScreen()),
                            ),
                            icon: const Icon(Icons.notifications_outlined),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SliverPadding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    sliver: SliverGrid(
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        mainAxisSpacing: 12,
                        crossAxisSpacing: 12,
                        childAspectRatio: 1.35,
                      ),
                      delegate: SliverChildListDelegate([
                        FlSummaryCard(label: 'Uploaded', value: '${_summary!.totalDocuments}', icon: Icons.upload_file),
                        FlSummaryCard(
                          label: 'System Approved',
                          value: '${_summary!.systemApproved}',
                          icon: Icons.verified_outlined,
                        ),
                        FlSummaryCard(
                          label: 'Needs Verification',
                          value: '${_summary!.needsVerification}',
                          icon: Icons.visibility_outlined,
                        ),
                        FlSummaryCard(
                          label: 'Needs Revision',
                          value: '${_summary!.needsRevision}',
                          icon: Icons.edit_note_outlined,
                        ),
                        FlSummaryCard(
                          label: 'KRA Progress',
                          value: '${_summary!.kraProgressPercent}%',
                          icon: Icons.donut_large_outlined,
                        ),
                      ]),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
                      child: Text(
                        'Quick actions',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.w700,
                              color: AppColors.deepNavy,
                            ),
                      ),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Row(
                        children: [
                          _QuickChip(
                            label: 'Upload',
                            icon: Icons.add,
                            onTap: () => Navigator.push(
                              context,
                              MaterialPageRoute<void>(builder: (_) => const UploadDocumentScreen()),
                            ),
                          ),
                          _QuickChip(label: 'My Documents', icon: Icons.folder, onTap: () => widget.onNavigateTab(1)),
                          _QuickChip(label: 'KRA', icon: Icons.fact_check, onTap: () => widget.onNavigateTab(2)),
                          _QuickChip(label: 'Rank', icon: Icons.insights, onTap: () => widget.onNavigateTab(3)),
                        ],
                      ),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
                      child: Text(
                        'KRA overview',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.w700,
                              color: AppColors.deepNavy,
                            ),
                      ),
                    ),
                  ),
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, i) {
                        final k = _kras[i];
                        return Card(
                          margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
                          child: ListTile(
                            title: Text(k.title, style: const TextStyle(fontWeight: FontWeight.w600)),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(k.status, style: const TextStyle(fontSize: 12)),
                                const SizedBox(height: 6),
                                LinearProgressIndicator(value: k.progress, minHeight: 6, borderRadius: BorderRadius.circular(4)),
                                Text(
                                  'Eligible pts: ${k.eligiblePointsLabel}',
                                  style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                                ),
                              ],
                            ),
                            trailing: TextButton(onPressed: () => widget.onNavigateTab(2), child: const Text('Details')),
                          ),
                        );
                      },
                      childCount: _kras.length,
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
                      child: Text(
                        'Recent activity',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
                      ),
                    ),
                  ),
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, i) {
                        final a = _activity[i];
                        return ListTile(
                          leading: const Icon(Icons.history, color: AppColors.brightBlue),
                          title: Text(a.message, style: const TextStyle(fontSize: 13)),
                          subtitle: Text(a.time),
                        );
                      },
                      childCount: _activity.length,
                    ),
                  ),
                  const SliverToBoxAdapter(child: SizedBox(height: 24)),
                ],
              ),
      ),
    );
  }
}

class _QuickChip extends StatelessWidget {
  const _QuickChip({required this.label, required this.icon, required this.onTap});

  final String label;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: ActionChip(
        avatar: Icon(icon, size: 18, color: AppColors.academicBlue),
        label: Text(label),
        onPressed: onTap,
      ),
    );
  }
}
