import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/document_status.dart';
import '../../models/kra_configuration_models.dart';
import '../../services/api/faculty_api.dart';
import '../../services/api/faculty_api_exception.dart';
import '../../widgets/fl_primary_button.dart';
import '../../widgets/fl_evaluation_period_card.dart';
import '../../services/evaluation_period_controller.dart';
import 'document_detail_screen.dart';

/// SET/SEF uploads for KRA I Criterion A only (Phase 2.1 backend integration).
class UploadDocumentScreen extends StatefulWidget {
  const UploadDocumentScreen({super.key, this.periodController});

  final EvaluationPeriodController? periodController;

  @override
  State<UploadDocumentScreen> createState() => _UploadDocumentScreenState();
}

class _UploadDocumentScreenState extends State<UploadDocumentScreen> {
  PlatformFile? _file;
  Uint8List? _previewBytes;
  final _titleController = TextEditingController();
  DocumentStatus? _progressState;
  bool _submitting = false;
  KraCriterionTarget? _criterionTarget;
  String? _configError;
  bool _loadingConfig = true;
  late final EvaluationPeriodController _periods =
      widget.periodController ?? EvaluationPeriodController.instance;

  @override
  void initState() {
    super.initState();
    _periods.addListener(_periodChanged);
    _periods.refresh();
    _loadCriterionConfig();
  }

  void _periodChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _loadCriterionConfig() async {
    try {
      final target = await FacultyApi.getKraICriterionA();
      if (!mounted) return;
      setState(() {
        _criterionTarget = target;
        _configError = null;
        _loadingConfig = false;
      });
    } on FacultyApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _configError = e.message;
        _loadingConfig = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _configError = 'Unable to load KRA I Criterion A configuration.';
        _loadingConfig = false;
      });
    }
  }

  @override
  void dispose() {
    _periods.removeListener(_periodChanged);
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
      _progressState = DocumentStatus.fileSelected;
    });
  }

  Future<void> _submit() async {
    if (!_periods.canSubmit) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Submissions are not permitted for the selected evaluation period.',
          ),
        ),
      );
      return;
    }
    final period = _periods.current;
    final target = _criterionTarget;
    if (period == null || target == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Evaluation period or KRA configuration unavailable.')),
      );
      return;
    }
    if (_file == null || _previewBytes == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select a PDF or image file.')),
      );
      return;
    }

    final periodId = int.tryParse(period.id);
    if (periodId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Invalid evaluation period identifier.')),
      );
      return;
    }

    setState(() {
      _submitting = true;
      _progressState = DocumentStatus.uploading;
    });

    try {
      if (!period.submissionsAllowedAt(_periods.now)) {
        throw FacultyApiException(
          'The evaluation period has closed.',
          errorCode: 'submission_closed',
        );
      }

      setState(() => _progressState = DocumentStatus.ocrProcessing);

      final detail = await FacultyApi.uploadDocument(
        periodId: periodId,
        criterionId: target.criterionId,
        title: _titleController.text.trim().isEmpty
            ? _file!.name
            : _titleController.text.trim(),
        fileName: _file!.name,
        bytes: _previewBytes!,
        mimeType: FacultyApi.mimeTypeForExtension(_file!.extension),
      );

      if (!mounted) return;
      setState(() {
        _submitting = false;
        _progressState = detail.status;
      });

      await Navigator.pushReplacement(
        context,
        MaterialPageRoute<void>(
          builder: (_) => DocumentDetailScreen(documentId: detail.id),
        ),
      );
    } on FacultyApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _submitting = false;
        _progressState = DocumentStatus.uploadFailed;
      });
      final message = e.isDuplicate
          ? e.message
          : e.isClosedPeriod
              ? e.message
              : e.message;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), duration: const Duration(seconds: 5)),
      );
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _submitting = false;
        _progressState = DocumentStatus.uploadFailed;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Upload failed. Check your connection and try again.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final target = _criterionTarget;
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
              IgnorePointer(
                ignoring: _submitting,
                child: FlEvaluationPeriodCard(controller: _periods),
              ),
              const SizedBox(height: 16),
              if (_loadingConfig)
                const LinearProgressIndicator()
              else if (_configError != null)
                Text(_configError!, style: const TextStyle(color: Colors.red))
              else if (target != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.bgLight,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        target.displayLabel,
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                      Text(
                        target.criterionName,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: AppColors.textMuted,
                            ),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'SET and SEF evidence only. Indicator A.1 / A.2 is classified from document content after upload.',
                        style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: _submitting ? null : _pickFile,
                icon: const Icon(Icons.attach_file),
                label: const Text('Select PDF or image'),
              ),
              if (_file != null) ...[
                const SizedBox(height: 12),
                Text(
                  'File: ${_file!.name} (${((_previewBytes?.length ?? 0) / 1024).toStringAsFixed(1)} KB)',
                ),
                if (_previewBytes != null && _file!.extension != 'pdf')
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.memory(
                        _previewBytes!,
                        height: 160,
                        fit: BoxFit.cover,
                      ),
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
                        Expanded(
                          child: Text(
                            'PDF selected — original file is sent to the server for OCR and validation.',
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
              const SizedBox(height: 20),
              TextField(
                controller: _titleController,
                decoration: const InputDecoration(labelText: 'Document title'),
              ),
              if (_progressState != null) ...[
                const SizedBox(height: 20),
                Text(
                  'Status: ${_progressState!.label}',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                if (_submitting) const LinearProgressIndicator(),
              ],
              const SizedBox(height: 24),
              FlPrimaryButton(
                label: _submitting
                    ? 'Uploading…'
                    : !_periods.canSubmit
                        ? 'Submissions unavailable'
                        : _configError != null
                            ? 'Configuration unavailable'
                            : 'Submit for OCR & validation',
                loading: _submitting,
                onPressed: _submitting ||
                        !_periods.canSubmit ||
                        _configError != null ||
                        target == null
                    ? null
                    : _submit,
              ),
              const SizedBox(height: 12),
              const Text(
                'Documents remain in Needs Verification until reviewer action. Automatic approval and point crediting are not enabled.',
                style: TextStyle(fontSize: 12, color: AppColors.textMuted),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
