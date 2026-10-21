import 'package:flutter/material.dart';
import '../../core/constants/app_disclaimers.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/fl_auth_shell.dart';
import '../../widgets/fl_logo.dart';
import '../../widgets/fl_primary_button.dart';
import '../../widgets/fl_text_field.dart';
import 'login_screen.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  static const routeName = '/forgot-password';

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  bool _loading = false;
  bool _submitted = false;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _loading = true;
      _submitted = false;
    });
    await Future<void>.delayed(const Duration(milliseconds: 650));
    if (!mounted) return;
    setState(() {
      _loading = false;
      _submitted = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return FlAuthShell(
      showBack: true,
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            const FlLogo(size: 34, variant: FlLogoVariant.lockup),
            const SizedBox(height: 20),
            Text(
              'Forgot Password',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: AppColors.primaryNavy,
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              'Enter your institutional email to request account recovery.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textMuted,
                    height: 1.45,
                  ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.bgLight,
                borderRadius: BorderRadius.circular(12),
                border: Border(left: BorderSide(color: AppColors.accentCyan, width: 4)),
              ),
              child: Text(
                'Mock mode: no reset email is sent until Flask authentication and mail delivery are integrated.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppColors.textMuted,
                      height: 1.45,
                    ),
              ),
            ),
            const SizedBox(height: 18),
            FlTextField(
              label: 'Email Address',
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.done,
              autofillHints: const [AutofillHints.email],
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'Enter your email';
                final email = v.trim();
                if (!RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email)) {
                  return 'Enter a valid email address';
                }
                return null;
              },
            ),
            if (_submitted) ...[
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFECFDF5),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFA7F3D0)),
                ),
                child: Text(
                  'Mock mode: recovery request noted for ${_email.text.trim()}. No email was sent.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: const Color(0xFF047857),
                        height: 1.45,
                      ),
                ),
              ),
            ],
            const SizedBox(height: 22),
            FlPrimaryButton(label: 'Submit Request', loading: _loading, onPressed: _submit),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () {
                if (Navigator.of(context).canPop()) {
                  Navigator.of(context).pop();
                } else {
                  Navigator.of(context).pushReplacementNamed(LoginScreen.routeName);
                }
              },
              child: const Text('Back to Login'),
            ),
            const SizedBox(height: 4),
            Text(
              AppDisclaimers.shortDisclaimer,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(color: AppColors.textMuted),
            ),
          ],
        ),
      ),
    );
  }
}
