import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';

class OcrResultsScreen extends StatelessWidget {
  const OcrResultsScreen({super.key, required this.detail});

  final DocumentDetail detail;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('OCR Extraction')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'Extracted via Tesseract on Flask backend when integrated. Below is mock UI data.',
            style: TextStyle(color: AppColors.textMuted, fontSize: 13),
          ),
          const SizedBox(height: 16),
          Text('Status: ${detail.ocrStatus}'),
          const SizedBox(height: 12),
          Text('Extracted text', style: Theme.of(context).textTheme.titleSmall),
          Text(detail.extractedText),
          const SizedBox(height: 16),
          Text('Recognized fields', style: Theme.of(context).textTheme.titleSmall),
          ...detail.ocrFields.map((e) => ListTile(title: Text(e.key), subtitle: Text(e.value), dense: true)),
          if (detail.ocrGaps.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('Uncertain / missing', style: Theme.of(context).textTheme.titleSmall),
            ...detail.ocrGaps.map((g) => Text('• $g')),
          ],
        ],
      ),
    );
  }
}
