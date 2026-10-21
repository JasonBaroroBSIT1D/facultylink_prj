import 'package:flutter/material.dart';
import '../../core/constants/app_disclaimers.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/fl_gradient_background.dart';
import '../../widgets/fl_logo.dart';
import '../../widgets/fl_primary_button.dart';
import '../../widgets/welcome_illustration.dart';
import '../auth/login_screen.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  static const routeName = '/';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: FlGradientBackground(
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              return SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight - 32),
                  child: Column(
                    children: [
                      const SizedBox(height: 8),
                      const FlLogo(size: 52),
                      const SizedBox(height: 24),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.fromLTRB(24, 32, 24, 28),
                        decoration: BoxDecoration(
                          color: AppColors.white,
                          borderRadius: BorderRadius.circular(28),
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.primaryNavy.withValues(alpha: 0.18),
                              blurRadius: 32,
                              offset: const Offset(0, 12),
                            ),
                          ],
                        ),
                        child: Column(
                          children: [
                            const FlLogo(size: 56, showLabel: false),
                            const SizedBox(height: 12),
                            Text(
                              AppDisclaimers.systemName,
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                    color: AppColors.primaryNavy,
                                    fontWeight: FontWeight.w700,
                                  ),
                            ),
                            const SizedBox(height: 20),
                            const WelcomeIllustration(),
                            const SizedBox(height: 20),
                            Text(
                              'Organize evidence. Review KRA assessment progress.',
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                    color: AppColors.primaryNavy,
                                    fontWeight: FontWeight.w800,
                                    height: 1.2,
                                  ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              'An academic self-assessment platform that helps faculty members organize supporting documents, '
                              'review their KRA performance, and explore simulated academic rank outcomes.',
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: AppColors.textMuted,
                                    height: 1.5,
                                  ),
                            ),
                            const SizedBox(height: 28),
                            FlPrimaryButton(
                              label: 'Get Started',
                              onPressed: () {
                                Navigator.of(context).pushReplacementNamed(LoginScreen.routeName);
                              },
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}
