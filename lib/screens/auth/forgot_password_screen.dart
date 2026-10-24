import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/constants/app_disclaimers.dart';
import '../../core/theme/app_colors.dart';
import '../../services/auth/auth_api.dart';
import '../../widgets/fl_auth_shell.dart';
import '../../widgets/fl_logo.dart';
import '../../widgets/fl_primary_button.dart';
import '../../widgets/fl_text_field.dart';
import 'login_screen.dart';
import 'password_reset_success_screen.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  static const routeName = '/forgot-password';

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  int _step = 0;
  final _email = TextEditingController();
  final _otp = TextEditingController();
  final _newPassword = TextEditingController();
  final _confirm = TextEditingController();
  bool _loading = false;
  String _resetGrant = '';
  int _resendCooldown = 0;
  Timer? _cooldownTimer;

  @override
  void dispose() {
    _email.dispose();
    _otp.dispose();
    _newPassword.dispose();
    _confirm.dispose();
    _cooldownTimer?.cancel();
    super.dispose();
  }

  void _startCooldown() {
    setState(() => _resendCooldown = 60);
    _cooldownTimer?.cancel();
    _cooldownTimer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) return;
      if (_resendCooldown <= 1) {
        t.cancel();
        setState(() => _resendCooldown = 0);
      } else {
        setState(() => _resendCooldown -= 1);
      }
    });
  }

  Future<void> _sendOtp() async {
    if (_email.text.trim().isEmpty) return;
    setState(() => _loading = true);
    try {
      final message = await AuthApi.requestPasswordResetOtp(_email.text);
      if (!mounted) return;
      setState(() => _step = 1);
      _startCooldown();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } on AuthException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _resendOtp() async {
    if (_resendCooldown > 0) return;
    setState(() => _loading = true);
    try {
      await AuthApi.resendPasswordResetOtp(_email.text);
      if (!mounted) return;
      _startCooldown();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('A new verification code was sent.')),
      );
    } on AuthException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _verifyOtp() async {
    setState(() => _loading = true);
    try {
      _resetGrant = await AuthApi.verifyPasswordResetOtp(_email.text, _otp.text);
      if (!mounted) return;
      setState(() => _step = 2);
    } on AuthException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _completeReset() async {
    if (_newPassword.text != _confirm.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Passwords do not match.')),
      );
      return;
    }
    setState(() => _loading = true);
    try {
      await AuthApi.completePasswordReset(
        email: _email.text,
        resetGrant: _resetGrant,
        newPassword: _newPassword.text,
        confirmPassword: _confirm.text,
      );
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(PasswordResetSuccessScreen.routeName);
    } on AuthException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

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
            _step == 0
                ? 'Forgot Password'
                : _step == 1
                    ? 'Verify Code'
                    : 'New Password',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: AppColors.primaryNavy,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            _step == 0
                ? 'Enter your registered email to receive a 6-digit verification code (expires in 5 minutes).'
                : _step == 1
                    ? 'Enter the code sent to your email.'
                    : 'Choose a new password for your account.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textMuted, height: 1.45),
          ),
          const SizedBox(height: 18),
          if (_step == 0) ...[
            FlTextField(
              label: 'Email Address',
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              autofillHints: const [AutofillHints.email],
            ),
            const SizedBox(height: 22),
            FlPrimaryButton(label: 'Send Verification Code', loading: _loading, onPressed: _sendOtp),
          ],
          if (_step == 1) ...[
            FlTextField(
              label: '6-Digit Code',
              controller: _otp,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(6)],
            ),
            if (_resendCooldown > 0)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  'Resend available in $_resendCooldown s',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textMuted),
                ),
              ),
            const SizedBox(height: 16),
            FlPrimaryButton(label: 'Verify Code', loading: _loading, onPressed: _verifyOtp),
            TextButton(
              onPressed: _resendCooldown > 0 || _loading ? null : _resendOtp,
              child: const Text('Resend Code'),
            ),
          ],
          if (_step == 2) ...[
            FlTextField(label: 'New Password', controller: _newPassword, obscureText: true),
            const SizedBox(height: 12),
            FlTextField(label: 'Confirm Password', controller: _confirm, obscureText: true),
            const SizedBox(height: 22),
            FlPrimaryButton(label: 'Save New Password', loading: _loading, onPressed: _completeReset),
          ],
          const SizedBox(height: 8),
          TextButton(
            onPressed: () => Navigator.of(context).pushReplacementNamed(LoginScreen.routeName),
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
    );
  }
}
