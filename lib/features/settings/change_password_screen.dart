import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../screens/welcome/welcome_screen.dart';
import '../../services/auth/auth_api.dart';
import '../../widgets/fl_primary_button.dart';
import '../../widgets/fl_text_field.dart';

class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({super.key});

  static const routeName = '/settings/change-password';

  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _current = TextEditingController();
  final _next = TextEditingController();
  final _confirm = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    _confirm.dispose();
    super.dispose();
  }

  String? _validateNew(String? value) {
    final password = value ?? '';
    if (password.length < 8) return 'Password must be at least 8 characters.';
    if (!RegExp(r'[A-Za-z]').hasMatch(password)) {
      return 'Password must include at least one letter.';
    }
    if (!RegExp(r'\d').hasMatch(password)) {
      return 'Password must include at least one number.';
    }
    return null;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _busy = true);
    try {
      await AuthApi.changePassword(_current.text, _next.text);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Password updated. Please sign in again.')),
      );
      await AuthApi.logout();
      if (!mounted) return;
      Navigator.of(context).pushNamedAndRemoveUntil(WelcomeScreen.routeName, (_) => false);
    } on AuthException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Password & Security')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        children: [
          Text(
            'Change your password to keep your account secure.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textMuted, fontSize: 14),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    FlTextField(
                      label: 'Current password',
                      controller: _current,
                      obscureText: true,
                      autofillHints: const [AutofillHints.password],
                      validator: (v) => (v == null || v.isEmpty) ? 'Enter your current password.' : null,
                    ),
                    const SizedBox(height: 12),
                    FlTextField(
                      label: 'New password',
                      controller: _next,
                      obscureText: true,
                      autofillHints: const [AutofillHints.newPassword],
                      validator: _validateNew,
                    ),
                    const SizedBox(height: 12),
                    FlTextField(
                      label: 'Confirm new password',
                      controller: _confirm,
                      obscureText: true,
                      autofillHints: const [AutofillHints.newPassword],
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'Confirm your new password.';
                        if (v != _next.text) return 'Passwords do not match.';
                        return null;
                      },
                    ),
                    const SizedBox(height: 14),
                    _PasswordRules(),
                    const SizedBox(height: 18),
                    FlPrimaryButton(
                      label: _busy ? 'Updating…' : 'Change Password',
                      onPressed: _busy ? null : _submit,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PasswordRules extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.bgLight,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'PASSWORD REQUIREMENTS',
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: AppColors.textMuted,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.6,
                ),
          ),
          const SizedBox(height: 6),
          const Text('• At least 8 characters', style: TextStyle(fontSize: 13, color: AppColors.textMuted)),
          const Text('• At least one letter (A–Z or a–z)', style: TextStyle(fontSize: 13, color: AppColors.textMuted)),
          const Text('• At least one number (0–9)', style: TextStyle(fontSize: 13, color: AppColors.textMuted)),
        ],
      ),
    );
  }
}
