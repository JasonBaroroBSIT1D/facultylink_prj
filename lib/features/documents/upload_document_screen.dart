import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/document_status.dart';
import '../../core/kra/kra_structure.dart';
import '../../services/mock/faculty_mock_data.dart';
import '../../widgets/fl_primary_button.dart';

class UploadDocumentScreen extends StatefulWidget {
  const UploadDocumentScreen({super.key});

  @override
  State<UploadDocumentScreen> createState() => _UploadDocumentScreenState();
}

class _UploadDocumentScreenState extends State<UploadDocumentScreen> {
  PlatformFile? _file;
  Uint8List? _previewBytes;
  final _titleController = TextEditingController();
  String? _kra;
  String? _criterion;
  DocumentStatus? _demoState;
  bool _simulating = false;

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final f = await FilePicker.pickFile(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'png', 'jpg', 'jpeg'],
    );
    if (f == null) return;
    final bytes = await f.readAsBytes();
    if (!mounted) return;
    setState(() {
      _file = f;
      _previewBytes = bytes;
      _titleController.text = f.name.replaceAll(RegExp(r'\.[^.]+$'), '');
      _demoState = DocumentStatus.fileSelected;
    });
  }

  Future<void> _simulateSubmit() async {
    if (_file == null || _kra == null || _criterion == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select file, KRA, and criterion.')),
      );
      return;
    }
    setState(() => _simulating = true);
    final steps = [
      DocumentStatus.uploading,
      DocumentStatus.ocrProcessing,
      DocumentStatus.classifying,
      DocumentStatus.validating,
      DocumentStatus.systemApproved,
    ];
    for (final s in steps) {
      if (!mounted) return;
      setState(() => _demoState = s);
      await Future<void>.delayed(const Duration(milliseconds: 700));
    }
    if (!mounted) return;
    setState(() => _simulating = false);
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Mock workflow complete'),
        content: const Text(
          'UI demonstration only. Indicator classification and approval come from the Flask rule engine — not saved locally.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK')),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.pop(context);
            },
            child: const Text('Done'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Upload Document')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 16,
            bottom: 16 + MediaQuery.viewInsetsOf(context).bottom,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              OutlinedButton.icon(onPressed: _pickFile, icon: const Icon(Icons.attach_file), label: const Text('Select PDF or image')),
              if (_file != null) ...[
                const SizedBox(height: 12),
                Text(
                  'File: ${_file!.name} (${((_file!.lengthSync() ?? _previewBytes?.length ?? 0) / 1024).toStringAsFixed(1)} KB)',
                ),
                if (_previewBytes != null && _file!.extension != 'pdf')
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.memory(_previewBytes!, height: 160, fit: BoxFit.cover),
                    ),
                  ),
                if (_file!.extension == 'pdf')
                  Container(
                    margin: const EdgeInsets.only(top: 12),
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: AppColors.bgLight,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.picture_as_pdf, color: AppColors.academicBlue, size: 40),
                        SizedBox(width: 12),
                        Expanded(child: Text('PDF selected — original preview via backend viewer when integrated.')),
                      ],
                    ),
                  ),
              ],
              const SizedBox(height: 20),
              TextField(
                controller: _titleController,
                decoration: const InputDecoration(labelText: 'Document title'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _kra,
                decoration: const InputDecoration(labelText: 'KRA'),
                items: KraStructure.kraOptions.map((k) => DropdownMenuItem(value: k, child: Text(k))).toList(),
                onChanged: (v) => setState(() {
                  _kra = v;
                  _criterion = null;
                }),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _criterion,
                decoration: const InputDecoration(labelText: 'Criterion'),
                items: (_kra != null ? FacultyMockData.criterionOptions[_kra!]! : <String>[])
                    .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                    .toList(),
                onChanged: _kra == null ? null : (v) => setState(() => _criterion = v),
              ),
              const SizedBox(height: 8),
              Text(
                'Indicator will be classified by the backend from document content (mock UI).',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textMuted),
              ),
              if (_demoState != null) ...[
                const SizedBox(height: 20),
                Text('Processing state (demo): ${_demoState!.label}', style: const TextStyle(fontWeight: FontWeight.w600)),
                if (_simulating) const LinearProgressIndicator(),
              ],
              const SizedBox(height: 24),
              FlPrimaryButton(
                label: _simulating ? 'Processing…' : 'Submit (mock workflow)',
                loading: _simulating,
                onPressed: _simulating ? null : _simulateSubmit,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
