import 'package:flutter/material.dart';
import '../core/constants/app_assets.dart';
import '../core/theme/app_colors.dart';

enum FlLogoVariant { full, emblem, lockup }

/// Official FacultyLink branding using [AppAssets.facultyLinkLogo].
class FlLogo extends StatelessWidget {
  const FlLogo({
    super.key,
    this.size = 40,
    this.variant = FlLogoVariant.lockup,
    this.showLabel = true,
    this.light = false,
  });

  final double size;
  final FlLogoVariant variant;
  final bool showLabel;
  final bool light;

  FlLogoVariant get _mode => !showLabel ? FlLogoVariant.emblem : variant;

  @override
  Widget build(BuildContext context) {
    switch (_mode) {
      case FlLogoVariant.emblem:
        return _Emblem(size: size);
      case FlLogoVariant.full:
        return Image.asset(
          AppAssets.facultyLinkLogo,
          width: size * 2.8,
          fit: BoxFit.contain,
          filterQuality: FilterQuality.medium,
        );
      case FlLogoVariant.lockup:
        return _BrandLockup(size: size, light: light);
    }
  }
}

class _Emblem extends StatelessWidget {
  const _Emblem({required this.size});

  final double size;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(size * 0.22),
      child: Image.asset(
        AppAssets.facultyLinkLogo,
        width: size,
        height: size,
        fit: BoxFit.cover,
        alignment: const Alignment(0, -0.58),
        filterQuality: FilterQuality.medium,
      ),
    );
  }
}

class _BrandLockup extends StatelessWidget {
  const _BrandLockup({required this.size, required this.light});

  final double size;
  final bool light;

  @override
  Widget build(BuildContext context) {
    final tagStyle = TextStyle(
      fontSize: size * 0.2,
      fontWeight: FontWeight.w500,
      letterSpacing: 0.04,
      color: light ? Colors.white.withValues(alpha: 0.78) : AppColors.textMuted,
    );

    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        _Emblem(size: size),
        SizedBox(width: size * 0.28),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            RichText(
              text: TextSpan(
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: size * 0.42,
                  height: 1,
                  letterSpacing: -0.02,
                ),
                children: [
                  TextSpan(
                    text: 'Faculty',
                    style: TextStyle(color: light ? AppColors.white : AppColors.primaryNavy),
                  ),
                  TextSpan(
                    text: 'Link',
                    style: TextStyle(color: light ? AppColors.accentCyan : AppColors.primaryBlue),
                  ),
                ],
              ),
            ),
            Text('Self-Assessment & Rank Simulation', style: tagStyle),
          ],
        ),
      ],
    );
  }
}
