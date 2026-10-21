import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/document_status.dart';

class FlStatusBadge extends StatelessWidget {
  const FlStatusBadge({super.key, required this.status});

  final DocumentStatus status;

  Color get _bg {
    switch (status) {
      case DocumentStatus.systemApproved:
        return const Color(0xFFE6F7ED);
      case DocumentStatus.needsVerification:
      case DocumentStatus.needsRevision:
      case DocumentStatus.validating:
        return const Color(0xFFFFF4E5);
      case DocumentStatus.rejected:
      case DocumentStatus.uploadFailed:
        return const Color(0xFFFEF2F2);
      default:
        return AppColors.bgLight;
    }
  }

  Color get _fg {
    switch (status) {
      case DocumentStatus.systemApproved:
        return const Color(0xFF137333);
      case DocumentStatus.needsVerification:
      case DocumentStatus.needsRevision:
      case DocumentStatus.validating:
        return const Color(0xFFB54708);
      case DocumentStatus.rejected:
      case DocumentStatus.uploadFailed:
        return const Color(0xFFB42318);
      default:
        return AppColors.academicBlue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: _bg, borderRadius: BorderRadius.circular(999)),
      child: Text(
        status.label,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: _fg),
      ),
    );
  }
}
