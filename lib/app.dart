import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'features/shell/main_shell.dart';
import 'screens/auth/forgot_password_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/welcome/welcome_screen.dart';

class FacultyLinkApp extends StatelessWidget {
  const FacultyLinkApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FacultyLink',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      initialRoute: WelcomeScreen.routeName,
      routes: {
        WelcomeScreen.routeName: (_) => const WelcomeScreen(),
        LoginScreen.routeName: (_) => const LoginScreen(),
        ForgotPasswordScreen.routeName: (_) => const ForgotPasswordScreen(),
        MainShell.routeName: (_) => const MainShell(),
      },
    );
  }
}
