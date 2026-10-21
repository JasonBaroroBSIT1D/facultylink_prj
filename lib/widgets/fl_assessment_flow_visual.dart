import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';

/// Lightweight document → assessment visual for the welcome screen.
class FlAssessmentFlowVisual extends StatelessWidget {
  const FlAssessmentFlowVisual({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 132,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _node(Icons.description_outlined, 'Documents'),
          _connector(),
          _node(Icons.fact_check_outlined, 'KRA Review'),
          _connector(),
          _node(Icons.insights_outlined, 'Simulation'),
        ],
      ),
    );
  }

  Widget _connector() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6),
      child: Container(
        width: 28,
        height: 2,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              AppColors.accentCyan.withValues(alpha: 0.2),
              AppColors.accentCyan.withValues(alpha: 0.85),
            ],
          ),
        ),
      ),
    );
  }

  Widget _node(IconData icon, String label) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            color: AppColors.white.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.white.withValues(alpha: 0.22)),
          ),
          child: Icon(icon, color: AppColors.accentCyan, size: 26),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.88),
            fontSize: 11,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.02,
          ),
        ),
      ],
    );
  }
}
