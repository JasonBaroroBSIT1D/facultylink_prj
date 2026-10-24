import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../services/auth/auth_api.dart';
import '../../widgets/fl_auth_shell.dart';
import '../../widgets/fl_logo.dart';
import '../../widgets/fl_primary_button.dart';
import '../../widgets/fl_text_field.dart';
import 'login_screen.dart';

class MandatoryChangePasswordScreen extends StatefulWidget {
  const MandatoryChangePasswordScreen({super.key});

  static const routeName = '/mandatory-change-password';

  @override
  State<MandatoryChangePasswordScreen> createState() => _MandatoryChangePasswordScreenState();
}

class _MandatoryChangePasswordScreenState extends State<MandatoryChangePasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _temp = TextEditingController();
  final _newPassword = TextEditingController();
  final _confirm = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _temp.dispose();
    _newPassword.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await AuthApi.completeMandatoryPasswordChange(
        temporaryPassword: _temp.text,
        newPassword: _newPassword.text,
        confirmPassword: _confirm.text,
      );
      if (!mounted) return;
      Navigator.of(context).pushNamedAndRemoveUntil(LoginScreen.routeName, (_) => false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Password updated. Please sign in again.')),
      );
    } on AuthException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Unable to reach the FacultyLink API.')),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FlAuthShell(
      showBack: false,
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            const FlLogo(size: 34, variant: FlLogoVariant.lockup),
            const SizedBox(height: 20),
            Text(
              'Change Your Password',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: AppColors.primaryNavy,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              'Use the temporary password from your welcome email, then choose a new secure password.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textMuted, height: 1.45),
            ),
            const SizedBox(height: 18),
            FlTextField(
              label: 'Temporary Password',
              controller: _temp,
              obscureText: true,
              validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
            ),
            const SizedBox(height: 12),
            FlTextField(
              label: 'New Password',
              controller: _newPassword,
              obscureText: true,
              validator: (v) {
                if (v == null || v.length < 8) return 'At least 8 characters';
                if (!RegExp(r'[A-Za-z]').hasMatch(v) || !RegExp(r'\d').hasMatch(v)) {
                  return 'Include letters and numbers';
                }
                return null;
              },
            ),
            const SizedBox(height: 12),
            FlTextField(
              label: 'Confirm New Password',
              controller: _confirm,
              obscureText: true,
              validator: (v) => v != _newPassword.text ? 'Passwords do not match' : null,
            ),
            const SizedBox(height: 22),
            FlPrimaryButton(label: 'Update Password', loading: _loading, onPressed: _submit),
          ],
        ),
      ),
    );
  }
}
