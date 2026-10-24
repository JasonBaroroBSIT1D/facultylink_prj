import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../core/config/api_config.dart';
import 'auth_session.dart';

class AuthUser {
  AuthUser({
    required this.userId,
    required this.email,
    required this.role,
    required this.fullName,
    this.facultyProfile,
    this.mustChangePassword = false,
  });

  final int userId;
  final String email;
  final String role;
  final String fullName;
  final Map<String, dynamic>? facultyProfile;
  final bool mustChangePassword;

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      userId: json['user_id'] as int,
      email: json['email'] as String,
      role: json['role'] as String,
      fullName: json['full_name'] as String,
      facultyProfile: json['faculty_profile'] as Map<String, dynamic>?,
      mustChangePassword: json['must_change_password'] == true || json['must_set_password'] == true,
    );
  }
}

class LoginResult {
  LoginResult({required this.user, required this.mustChangePassword});

  final AuthUser user;
  final bool mustChangePassword;
}

class AuthApi {
  static Uri _uri(String path) => Uri.parse('${ApiConfig.baseUrl}$path');

  static Future<LoginResult> login(String email, String password) async {
    final response = await http.post(
      _uri('/api/v1/auth/login'),
      headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
      body: jsonEncode({
        'email': email.trim(),
        'password': password,
        'client': 'mobile',
      }),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode != 200) {
      throw AuthException(body['message'] as String? ?? 'Sign in failed.');
    }
    final token = body['access_token'] as String?;
    if (token == null || token.isEmpty) {
      throw AuthException('Authentication token missing from server response.');
    }
    await AuthSession.instance.saveToken(token);
    final user = AuthUser.fromJson(body['user'] as Map<String, dynamic>);
    final mustChange = body['must_change_password'] == true || user.mustChangePassword;
    return LoginResult(user: user, mustChangePassword: mustChange);
  }

  static Future<void> completeMandatoryPasswordChange({
    required String temporaryPassword,
    required String newPassword,
    required String confirmPassword,
  }) async {
    final token = await AuthSession.instance.readToken();
    if (token == null) throw AuthException('Not signed in.');
    final response = await http.post(
      _uri('/api/v1/auth/complete-mandatory-password'),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'temporary_password': temporaryPassword,
        'new_password': newPassword,
        'confirm_password': confirmPassword,
      }),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode != 200) {
      throw AuthException(body['message'] as String? ?? 'Password change failed.');
    }
    await AuthSession.instance.clear();
  }

  static Future<String> requestPasswordResetOtp(String email) async {
    final response = await http.post(
      _uri('/api/v1/auth/forgot-password'),
      headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
      body: jsonEncode({'email': email.trim()}),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 429) {
      throw AuthException(body['message'] as String? ?? 'Too many requests.');
    }
    if (response.statusCode != 200) {
      throw AuthException(body['message'] as String? ?? 'Unable to send verification code.');
    }
    var message = body['message'] as String? ?? 'If an account exists, a verification code was sent.';
    final delivery = body['email_delivery'] as Map<String, dynamic>?;
    if (delivery != null && delivery['sent'] == false) {
      message = '$message Email delivery failed — try again later.';
    }
    return message;
  }

  static Future<String> resendPasswordResetOtp(String email) async {
    final response = await http.post(
      _uri('/api/v1/auth/forgot-password/resend-otp'),
      headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
      body: jsonEncode({'email': email.trim()}),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 429) {
      throw AuthException(body['message'] as String? ?? 'Please wait before resending.');
    }
    if (response.statusCode != 200) {
      throw AuthException(body['message'] as String? ?? 'Unable to resend code.');
    }
    return body['message'] as String? ?? 'Verification code sent.';
  }

  static Future<String> verifyPasswordResetOtp(String email, String otp) async {
    final response = await http.post(
      _uri('/api/v1/auth/forgot-password/verify-otp'),
      headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
      body: jsonEncode({'email': email.trim(), 'otp': otp.trim()}),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode != 200) {
      throw AuthException(body['message'] as String? ?? 'Invalid verification code.');
    }
    return body['reset_grant'] as String? ?? '';
  }

  static Future<String> completePasswordReset({
    required String email,
    required String resetGrant,
    required String newPassword,
    required String confirmPassword,
  }) async {
    final response = await http.post(
      _uri('/api/v1/auth/forgot-password/complete'),
      headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
      body: jsonEncode({
        'email': email.trim(),
        'reset_grant': resetGrant,
        'new_password': newPassword,
        'confirm_password': confirmPassword,
      }),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode != 200) {
      throw AuthException(body['message'] as String? ?? 'Unable to save password.');
    }
    return body['message'] as String? ?? 'Password updated. You can now sign in.';
  }

  static Future<AuthUser> me() async {
    final token = await AuthSession.instance.readToken();
    if (token == null) throw AuthException('Not signed in.');
    final response = await http.get(
      _uri('/api/v1/auth/me'),
      headers: {
        'Accept': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 403 && body['error'] == 'password_change_required') {
      throw AuthException(body['message'] as String? ?? 'Password change required.');
    }
    if (response.statusCode != 200) {
      throw AuthException(body['message'] as String? ?? 'Session expired.');
    }
    return AuthUser.fromJson(body['user'] as Map<String, dynamic>);
  }

  static Future<void> logout() async {
    final token = await AuthSession.instance.readToken();
    if (token != null) {
      await http.post(
        _uri('/api/v1/auth/logout'),
        headers: {
          'Accept': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );
    }
    await AuthSession.instance.clear();
  }

  static Future<void> changePassword(String current, String next) async {
    final token = await AuthSession.instance.readToken();
    if (token == null) throw AuthException('Not signed in.');
    final response = await http.post(
      _uri('/api/v1/auth/change-password'),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({'current_password': current, 'new_password': next}),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode != 200) {
      throw AuthException(body['message'] as String? ?? 'Password change failed.');
    }
    await AuthSession.instance.clear();
  }
}

class AuthException implements Exception {
  AuthException(this.message);
  final String message;
  @override
  String toString() => message;
}
