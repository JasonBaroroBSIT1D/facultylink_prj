import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter/material.dart';

import '../../screens/auth/forgot_password_screen.dart';
import '../../screens/auth/setup_password_screen.dart';

/// Handles facultylink:// deep links — legacy setup tokens redirect to sign-in guidance.
class DeepLinkService {
  DeepLinkService._();

  static final DeepLinkService instance = DeepLinkService._();

  final AppLinks _appLinks = AppLinks();
  StreamSubscription<Uri>? _sub;
  GlobalKey<NavigatorState>? _navigatorKey;

  Future<void> init(GlobalKey<NavigatorState> navigatorKey) async {
    _navigatorKey = navigatorKey;
    final initial = await _appLinks.getInitialLink();
    if (initial != null) {
      _handleUri(initial);
    }
    _sub = _appLinks.uriLinkStream.listen(_handleUri);
  }

  void dispose() {
    _sub?.cancel();
  }

  void _handleUri(Uri uri) {
    final nav = _navigatorKey?.currentState;
    if (nav == null) return;

    final host = uri.host.toLowerCase();
    final path = uri.path.toLowerCase();
    final isReset = host == 'reset' || path.contains('reset');

    if (isReset) {
      nav.pushNamed(ForgotPasswordScreen.routeName);
      return;
    }

    final token = _extractToken(uri);
    nav.pushNamed(
      SetupPasswordScreen.routeName,
      arguments: token ?? '',
    );
  }

  String? _extractToken(Uri uri) {
    final q = uri.queryParameters['token'];
    if (q != null && q.trim().isNotEmpty) return q.trim();
    if (uri.fragment.startsWith('token=')) {
      return uri.fragment.substring(6).trim();
    }
    return null;
  }
}
