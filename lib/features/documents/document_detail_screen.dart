import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';
import '../../services/api/faculty_api.dart';
import '../../widgets/fl_status_badge.dart';
import 'ocr_results_screen.dart';
import 'validation_results_screen.dart';

class DocumentDetailScreen extends StatefulWidget {
  const DocumentDetailScreen({super.key, required this.documentId});

  final String documentId;

  @override
  State<DocumentDetailScreen> createState() => _DocumentDetailScreenState();
}

class _DocumentDetailScreenState extends State<DocumentDetailScreen> {
  DocumentDetail? _detail;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    FacultyApi.getDocumentDetail(widget.documentId).then((d) {
      if (!mounted) return;
      setState(() {
        _detail = d;
        _loading = false;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Document Detail')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(_detail!.title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 8),
                  FlStatusBadge(status: _detail!.status),
                  const SizedBox(height: 16),
                  _Section(
                    title: 'Original document',
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: AppColors.bgLight,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Column(
                        children: [
                          const Icon(Icons.picture_as_pdf, size: 48, color: AppColors.academicBlue),
                          const SizedBox(height: 8),
                          Text(_detail!.fileName, textAlign: TextAlign.center),
                          const Text(
                            'Original file preserved — not replaced by OCR text (mock).',
                            textAlign: TextAlign.center,
                            style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                          ),
                        ],
                      ),
                    ),
                  ),
                  _Section(
                    title: 'Classification',
                    child: Text(
                      '${_detail!.kra} → Criterion ${_detail!.criterion} → ${_detail!.detectedIndicator ?? "Pending"}',
                    ),
                  ),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => Navigator.push(
                            context,
                            MaterialPageRoute<void>(
                              builder: (_) => OcrResultsScreen(detail: _detail!),
                            ),
                          ),
                          child: const Text('OCR Results'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => Navigator.push(
                            context,
                            MaterialPageRoute<void>(
                              builder: (_) => ValidationResultsScreen(detail: _detail!),
                            ),
                          ),
                          child: const Text('Validation'),
                        ),
                      ),
                    ],
                  ),
                  if (_detail!.reviewerNote != null)
                    _Section(title: 'Reviewer feedback (mock)', child: Text(_detail!.reviewerNote!)),
                  _Section(
                    title: 'Status history',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: _detail!.statusHistory
                          .map((e) => Text('${e.key}: ${e.value}', style: const TextStyle(fontSize: 13)))
                          .toList(),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.deepNavy)),
          const SizedBox(height: 8),
          child,
        ],
      ),
    );
  }
}
