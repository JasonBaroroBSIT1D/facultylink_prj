import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/fl_auth_shell.dart';
import '../../widgets/fl_logo.dart';
import '../../widgets/fl_primary_button.dart';
import 'forgot_password_screen.dart';

/// Legacy reset links redirect to the OTP forgot-password flow.
class ResetPasswordScreen extends StatelessWidget {
  const ResetPasswordScreen({super.key, this.initialToken = ''});

  static const routeName = '/reset-password';

  final String initialToken;

  @override
  Widget build(BuildContext context) {
    return FlAuthShell(
      showBack: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          const FlLogo(size: 34, variant: FlLogoVariant.lockup),
          const SizedBox(height: 20),
          Text(
            'Reset Your Password',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: AppColors.primaryNavy,
                ),
          ),
          const SizedBox(height: 12),
          Text(
            'Password reset now uses a 6-digit verification code sent to your email. '
            'Continue below to request a code and choose a new password.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textMuted,
                  height: 1.45,
                ),
          ),
          const SizedBox(height: 22),
          FlPrimaryButton(
            label: 'Forgot Password',
            onPressed: () {
              Navigator.of(context).pushReplacementNamed(ForgotPasswordScreen.routeName);
            },
          ),
        ],
      ),
    );
  }
}
