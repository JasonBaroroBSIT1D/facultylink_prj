import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/fl_auth_shell.dart';
import '../../widgets/fl_logo.dart';
import '../../widgets/fl_primary_button.dart';
import 'forgot_password_screen.dart';
import 'login_screen.dart';

/// Legacy deep-link setup tokens are retired — use login + mandatory password change.
class SetupPasswordScreen extends StatelessWidget {
  const SetupPasswordScreen({super.key, this.token = ''});

  static const routeName = '/setup-password';

  final String token;

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
            'Use Your Temporary Password',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: AppColors.primaryNavy,
                ),
          ),
          const SizedBox(height: 12),
          Text(
            'Account setup links are no longer used. Sign in with the temporary password from your '
            'welcome email, then choose a new password on the next screen.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textMuted,
                  height: 1.45,
                ),
          ),
          const SizedBox(height: 22),
          FlPrimaryButton(
            label: 'Go to Sign In',
            onPressed: () {
              Navigator.of(context).pushReplacementNamed(LoginScreen.routeName);
            },
          ),
          const SizedBox(height: 10),
          TextButton(
            onPressed: () => Navigator.of(context).pushNamed(ForgotPasswordScreen.routeName),
            child: const Text('Forgot Password?'),
          ),
        ],
      ),
    );
  }
}
