import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';
import '../../services/api/faculty_api.dart';
import '../../services/api/faculty_api_exception.dart';
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
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final d = await FacultyApi.getDocumentDetail(widget.documentId);
      if (!mounted) return;
      setState(() {
        _detail = d;
        _loading = false;
      });
    } on FacultyApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Unable to load document.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Document Detail'),
        actions: [
          IconButton(onPressed: _load, icon: const Icon(Icons.refresh)),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _detail!.title,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 8),
                  FlStatusBadge(status: _detail!.status),
                  const SizedBox(height: 8),
                  Text(
                    'Server status reflects OCR and rule validation. Needs Verification does not mean credited or system-approved.',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textMuted),
                  ),
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
                          Icon(
                            _detail!.fileName.toLowerCase().endsWith('.pdf')
                                ? Icons.picture_as_pdf
                                : Icons.image,
                            size: 48,
                            color: AppColors.academicBlue,
                          ),
                          const SizedBox(height: 8),
                          Text(_detail!.fileName, textAlign: TextAlign.center),
                          const Text(
                            'Original file preserved on the server.',
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
                  _Section(
                    title: 'Validation summary',
                    child: Text(_detail!.validationSummary),
                  ),
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
