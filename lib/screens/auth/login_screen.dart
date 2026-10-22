import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../features/shell/main_shell.dart';
import '../../services/auth/auth_api.dart';
import '../../services/evaluation_period_controller.dart';
import '../../widgets/fl_auth_shell.dart';
import '../../widgets/fl_logo.dart';
import '../../widgets/fl_primary_button.dart';
import '../../widgets/fl_text_field.dart';
import 'forgot_password_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  static const routeName = '/login';

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _signIn() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _loading = true);
    try {
      final user = await AuthApi.login(
        _emailController.text,
        _passwordController.text,
      );
      if (!mounted) return;
      if (user.role != 'faculty') {
        await AuthApi.logout();
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Admin and reviewer accounts must use the web portal.'),
          ),
        );
        return;
      }
      if (!mounted) return;
      await EvaluationPeriodController.instance.refresh();
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(MainShell.routeName);
    } on AuthException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message)),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Unable to reach the FacultyLink API. Check your connection.'),
        ),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FlAuthShell(
      showBack: Navigator.of(context).canPop(),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            const FlLogo(size: 34, variant: FlLogoVariant.lockup),
            const SizedBox(height: 20),
            Text(
              'Welcome Back',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: AppColors.primaryNavy,
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              'Sign in to your faculty account',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textMuted),
            ),
            const SizedBox(height: 24),
            FlTextField(
              label: 'Email Address',
              controller: _emailController,
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.next,
              autofillHints: const [AutofillHints.email],
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'Enter your email';
                if (!v.contains('@')) return 'Enter a valid email';
                return null;
              },
            ),
            const SizedBox(height: 14),
            FlTextField(
              label: 'Password',
              controller: _passwordController,
              obscureText: true,
              textInputAction: TextInputAction.done,
              autofillHints: const [AutofillHints.password],
              validator: (v) {
                if (v == null || v.isEmpty) return 'Enter your password';
                return null;
              },
            ),
            const SizedBox(height: 6),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => Navigator.pushNamed(context, ForgotPasswordScreen.routeName),
                child: const Text('Forgot Password?'),
              ),
            ),
            const SizedBox(height: 8),
            FlPrimaryButton(label: 'Sign In', loading: _loading, onPressed: _signIn),
          ],
        ),
      ),
    );
  }
}
