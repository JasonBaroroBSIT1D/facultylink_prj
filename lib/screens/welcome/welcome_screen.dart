import 'package:flutter/material.dart';
import '../../core/constants/app_disclaimers.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/fl_assessment_flow_visual.dart';
import '../../widgets/fl_logo.dart';
import '../../widgets/fl_primary_button.dart';
import '../auth/login_screen.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  static const routeName = '/';

  @override
  Widget build(BuildContext context) {
    final headline = Theme.of(context).textTheme.headlineMedium?.copyWith(
          color: AppColors.white,
          fontWeight: FontWeight.w800,
          height: 1.15,
          letterSpacing: -0.02,
        );

    return Scaffold(
      backgroundColor: AppColors.primaryNavy,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 8),
              const FlLogo(size: 36, light: true),
              const Spacer(flex: 2),
              Text('Your Academic Growth,\nClearly Assessed.', style: headline),
              const SizedBox(height: 14),
              Text(
                AppDisclaimers.purpose,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.white.withValues(alpha: 0.82),
                      height: 1.55,
                    ),
              ),
              const SizedBox(height: 28),
              const FlAssessmentFlowVisual(),
              const Spacer(flex: 3),
              FlPrimaryButton(
                label: 'Get Started',
                onPressed: () {
                  Navigator.of(context).pushReplacementNamed(LoginScreen.routeName);
                },
              ),
              const SizedBox(height: 10),
              TextButton(
                onPressed: () => Navigator.of(context).pushNamed(LoginScreen.routeName),
                child: Text(
                  'Sign In',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.92),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                AppDisclaimers.shortDisclaimer,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Colors.white.withValues(alpha: 0.55),
                      height: 1.4,
                    ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}
