import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/faculty_models.dart';
import '../../services/api/faculty_api.dart';
import '../notifications/notifications_screen.dart';
import '../settings/settings_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  FacultyProfile? _profile;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    FacultyApi.getProfile().then((p) {
      if (!mounted) return;
      setState(() {
        _profile = p;
        _loading = false;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgLight,
      appBar: AppBar(
        title: const Text('Profile'),
        backgroundColor: AppColors.white,
        foregroundColor: AppColors.deepNavy,
        elevation: 0,
        actions: [
          IconButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute<void>(builder: (_) => const NotificationsScreen())),
            icon: const Icon(Icons.notifications_outlined),
          ),
          IconButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute<void>(builder: (_) => const SettingsScreen())),
            icon: const Icon(Icons.settings_outlined),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Center(
                  child: CircleAvatar(
                    radius: 48,
                    backgroundColor: AppColors.academicBlue,
                    child: Text(
                      _profile!.fullName.split(' ').map((e) => e[0]).take(2).join(),
                      style: const TextStyle(fontSize: 28, color: Colors.white, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Center(
                  child: Text(
                    _profile!.fullName,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                  ),
                ),
                const SizedBox(height: 24),
                _tile(Icons.badge_outlined, 'Faculty ID', _profile!.id),
                _tile(Icons.email_outlined, 'Email', _profile!.email),
                _tile(Icons.apartment_outlined, 'Department', _profile!.department),
                _tile(Icons.school_outlined, 'College', _profile!.college),
                _tile(Icons.workspace_premium_outlined, 'Current rank', _profile!.rank),
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Edit profile — awaiting Flask API.')),
                    );
                  },
                  icon: const Icon(Icons.edit_outlined),
                  label: const Text('Edit Profile'),
                ),
              ],
            ),
    );
  }

  Widget _tile(IconData icon, String label, String value) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(leading: Icon(icon, color: AppColors.academicBlue), title: Text(label), subtitle: Text(value)),
    );
  }
}
