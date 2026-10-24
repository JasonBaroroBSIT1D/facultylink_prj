import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/fl_auth_shell.dart';
import '../../widgets/fl_logo.dart';
import '../../widgets/fl_primary_button.dart';
import 'forgot_password_screen.dart';
import 'login_screen.dart';

/// Legacy invitation codes are retired — faculty use welcome-email temporary passwords.
class SetupAccountScreen extends StatelessWidget {
  const SetupAccountScreen({super.key});

  static const routeName = '/setup-account';

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
            'Sign In With Your Welcome Email',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: AppColors.primaryNavy,
                ),
          ),
          const SizedBox(height: 12),
          Text(
            'New faculty accounts no longer use setup codes. Open the welcome email from FacultyLink, '
            'sign in with your temporary password, then create a new password when prompted.',
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
