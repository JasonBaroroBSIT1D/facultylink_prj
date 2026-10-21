import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';
import '../../services/api/faculty_api.dart';
import '../../widgets/fl_empty_state.dart';
class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<AppNotification> _items = [];
  String? _typeFilter;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final list = await FacultyApi.listNotifications();
    if (!mounted) return;
    setState(() {
      _items = list;
      _loading = false;
    });
  }

  List<AppNotification> get _filtered {
    if (_typeFilter == null) return _items;
    return _items.where((n) => n.type == _typeFilter).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notifications')),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                FilterChip(
                  label: const Text('All'),
                  selected: _typeFilter == null,
                  onSelected: (_) => setState(() => _typeFilter = null),
                ),
                ...['document', 'kra', 'rank', 'reviewer'].map(
                  (t) => Padding(
                    padding: const EdgeInsets.only(left: 8),
                    child: FilterChip(
                      label: Text(t),
                      selected: _typeFilter == t,
                      onSelected: (_) => setState(() => _typeFilter = t),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _filtered.isEmpty
                    ? const FlEmptyState(message: 'No notifications.')
                    : ListView.builder(
                        itemCount: _filtered.length,
                        itemBuilder: (context, i) {
                          final n = _filtered[i];
                          return ListTile(
                            leading: Icon(
                              n.read ? Icons.notifications_none : Icons.notifications_active,
                              color: n.read ? AppColors.textMuted : AppColors.academicBlue,
                            ),
                            title: Text(n.title, style: TextStyle(fontWeight: n.read ? FontWeight.normal : FontWeight.w700)),
                            subtitle: Text('${n.body}\n${n.time}'),
                            isThreeLine: true,
                            onTap: () => showDialog<void>(
                              context: context,
                              builder: (ctx) => AlertDialog(
                                title: Text(n.title),
                                content: Text(n.body),
                                actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Close'))],
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
