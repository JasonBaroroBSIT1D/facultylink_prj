import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';

class FlGradientBackground extends StatelessWidget {
  const FlGradientBackground({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.brightBlue, AppColors.academicBlue, AppColors.deepNavy],
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            top: -80,
            right: -40,
            child: _Circle(size: 220, opacity: 0.12),
          ),
          Positioned(
            bottom: 120,
            left: -60,
            child: _Circle(size: 180, opacity: 0.1),
          ),
          Positioned(
            top: MediaQuery.sizeOf(context).height * 0.35,
            right: 40,
            child: _Circle(size: 90, opacity: 0.08),
          ),
          child,
        ],
      ),
    );
  }
}

class _Circle extends StatelessWidget {
  const _Circle({required this.size, required this.opacity});

  final double size;
  final double opacity;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.white.withValues(alpha: opacity),
      ),
    );
  }
}
