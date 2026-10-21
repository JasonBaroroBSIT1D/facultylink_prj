import 'package:flutter/material.dart';

/// FacultyLink brand palette — shared with the web portal (`admin_reviewer_web/css/tokens.css`).
abstract final class AppColors {
  static const primaryNavy = Color(0xFF082653);
  static const primaryBlue = Color(0xFF0866D9);
  static const accentCyan = Color(0xFF09B8F2);

  /// Legacy aliases used across existing widgets.
  static const academicBlue = primaryBlue;
  static const brightBlue = primaryBlue;
  static const deepNavy = primaryNavy;
  static const cyan = accentCyan;

  static const white = Color(0xFFFFFFFF);
  static const bgLight = Color(0xFFF5F8FC);
  static const textPrimary = Color(0xFF10233F);
  static const textMuted = Color(0xFF64748B);
  static const border = Color(0xFFDCE5F0);
}
