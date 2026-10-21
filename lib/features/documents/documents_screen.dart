import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/document_status.dart';
import '../../models/faculty_models.dart';
import '../../services/api/faculty_api.dart';
import '../../core/kra/kra_structure.dart';
import '../../widgets/fl_empty_state.dart';
import '../../widgets/fl_status_badge.dart';
import 'document_detail_screen.dart';
import 'upload_document_screen.dart';

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  List<FacultyDocument> _docs = [];
  String _search = '';
  String? _kraFilter;
  String? _criterionFilter;
  String? _statusFilter;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final docs = await FacultyApi.listDocuments();
    if (!mounted) return;
    setState(() {
      _docs = docs;
      _loading = false;
    });
  }

  List<FacultyDocument> get _filtered {
    return _docs.where((d) {
      final q = _search.toLowerCase();
      final matchQ = d.title.toLowerCase().contains(q) || d.fileName.toLowerCase().contains(q);
      final matchKra = _kraFilter == null || d.kra == _kraFilter;
      final matchCrit = _criterionFilter == null || d.criterion == _criterionFilter;
      final matchSt = _statusFilter == null || d.status.label == _statusFilter;
      return matchQ && matchKra && matchCrit && matchSt;
    }).toList()
      ..sort((a, b) => b.uploadedAt.compareTo(a.uploadedAt));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgLight,
      appBar: AppBar(
        title: const Text('My Documents'),
        backgroundColor: AppColors.white,
        foregroundColor: AppColors.deepNavy,
        elevation: 0,
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await Navigator.push(context, MaterialPageRoute<void>(builder: (_) => const UploadDocumentScreen()));
          _load();
        },
        icon: const Icon(Icons.upload_file),
        label: const Text('Upload'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                TextField(
                  decoration: InputDecoration(
                    hintText: 'Search documents',
                    prefixIcon: const Icon(Icons.search),
                    filled: true,
                    fillColor: AppColors.white,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
                  ),
                  onChanged: (v) => setState(() => _search = v),
                ),
                const SizedBox(height: 8),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      DropdownButton<String?>(
                        value: _kraFilter,
                        hint: const Text('KRA'),
                        items: [
                          const DropdownMenuItem(value: null, child: Text('All KRAs')),
                          ...KraStructure.kraOptions.map((k) => DropdownMenuItem(value: k, child: Text(k))),
                        ],
                        onChanged: (v) => setState(() {
                          _kraFilter = v;
                          if (!KraStructure.isValidPair(_kraFilter, _criterionFilter)) {
                            _criterionFilter = null;
                          }
                        }),
                      ),
                      const SizedBox(width: 8),
                      DropdownButton<String?>(
                        value: _criterionFilter,
                        hint: const Text('Criterion'),
                        items: [
                          const DropdownMenuItem(value: null, child: Text('All criteria')),
                          ...KraStructure.lettersFor(_kraFilter).map(
                            (c) => DropdownMenuItem(value: c, child: Text('Criterion $c')),
                          ),
                        ],
                        onChanged: _kraFilter == null ? null : (v) => setState(() => _criterionFilter = v),
                      ),
                      const SizedBox(width: 8),
                      DropdownButton<String?>(
                        value: _statusFilter,
                        hint: const Text('Status'),
                        items: const [
                          DropdownMenuItem(value: null, child: Text('All statuses')),
                          DropdownMenuItem(value: 'System Approved', child: Text('System Approved')),
                          DropdownMenuItem(value: 'Needs Verification', child: Text('Needs Verification')),
                        ],
                        onChanged: (v) => setState(() => _statusFilter = v),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _filtered.isEmpty
                    ? const FlEmptyState(message: 'No documents match your filters.')
                    : ListView.builder(
                        itemCount: _filtered.length,
                        itemBuilder: (context, i) {
                          final d = _filtered[i];
                          return Card(
                            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                            child: ListTile(
                              title: Text(d.title, maxLines: 2, overflow: TextOverflow.ellipsis),
                              subtitle: Text('${d.kra} · Criterion ${d.criterion}\n${d.detectedIndicator ?? "Indicator: pending classification"}'),
                              isThreeLine: true,
                              trailing: FlStatusBadge(status: d.status),
                              onTap: () => Navigator.push(
                                context,
                                MaterialPageRoute<void>(
                                  builder: (_) => DocumentDetailScreen(documentId: d.id),
                                ),
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
