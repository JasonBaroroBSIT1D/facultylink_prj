import 'package:flutter/material.dart';
import '../core/constants/app_assets.dart';

/// Official FacultyLink logo asset ([AppAssets.facultyLinkLogo]).
class FlLogo extends StatelessWidget {
  const FlLogo({super.key, this.size = 48, this.showLabel = true});

  final double size;
  final bool showLabel;

  @override
  Widget build(BuildContext context) {
    if (!showLabel) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(size * 0.16),
        child: Image.asset(
          AppAssets.facultyLinkLogo,
          width: size,
          height: size,
          fit: BoxFit.cover,
          alignment: const Alignment(0, -0.55),
          filterQuality: FilterQuality.medium,
        ),
      );
    }

    return Image.asset(
      AppAssets.facultyLinkLogo,
      width: size * 3.6,
      fit: BoxFit.contain,
      filterQuality: FilterQuality.medium,
    );
  }
}
