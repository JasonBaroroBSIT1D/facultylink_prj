import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/fl_auth_shell.dart';
import '../../widgets/fl_logo.dart';
import '../../widgets/fl_primary_button.dart';
import 'login_screen.dart';

class PasswordResetSuccessScreen extends StatelessWidget {
  const PasswordResetSuccessScreen({super.key});

  static const routeName = '/password-reset-success';

  @override
  Widget build(BuildContext context) {
    return FlAuthShell(
      showBack: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          const FlLogo(size: 34, variant: FlLogoVariant.lockup),
          const SizedBox(height: 20),
          Text(
            'Password Updated',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: AppColors.primaryNavy,
                ),
          ),
          const SizedBox(height: 12),
          Text(
            'Your password has been reset. Sign in with your new password.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textMuted, height: 1.45),
          ),
          const SizedBox(height: 24),
          FlPrimaryButton(
            label: 'Back to Sign In',
            onPressed: () => Navigator.of(context).pushNamedAndRemoveUntil(LoginScreen.routeName, (_) => false),
          ),
        ],
      ),
    );
  }
}
