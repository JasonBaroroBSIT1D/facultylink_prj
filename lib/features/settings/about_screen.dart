import 'package:flutter/material.dart';
import '../../core/constants/app_disclaimers.dart';
import '../../widgets/fl_logo.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('About FacultyLink')),
      body: const Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          children: [
            FlLogo(size: 56),
            SizedBox(height: 16),
            Text(AppDisclaimers.systemName, textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w600)),
            SizedBox(height: 8),
            Text(
              AppDisclaimers.rankSimulation,
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 12),
            Text('Version 1.0.0 (Phase 3 frontend)', style: TextStyle(fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
