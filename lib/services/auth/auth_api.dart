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
  });

  final int userId;
  final String email;
  final String role;
  final String fullName;
  final Map<String, dynamic>? facultyProfile;

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      userId: json['user_id'] as int,
      email: json['email'] as String,
      role: json['role'] as String,
      fullName: json['full_name'] as String,
      facultyProfile: json['faculty_profile'] as Map<String, dynamic>?,
    );
  }
}

class AuthApi {
  static Uri _uri(String path) => Uri.parse('${ApiConfig.baseUrl}$path');

  static Future<AuthUser> login(String email, String password) async {
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
    return AuthUser.fromJson(body['user'] as Map<String, dynamic>);
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
