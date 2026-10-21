import 'package:flutter/material.dart';
import '../../screens/welcome/welcome_screen.dart';
import '../../services/api/faculty_api.dart';
import '../../widgets/fl_primary_button.dart';
import '../../widgets/fl_text_field.dart';
import 'about_screen.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Account Settings')),
      body: ListView(
        children: [
          const ListTile(title: Text('Account Information'), subtitle: Text('Managed via Flask when integrated')),
          ListTile(
            title: const Text('Change Password'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showChangePassword(context),
          ),
          SwitchListTile(
            title: const Text('Notification preferences (mock)'),
            subtitle: const Text('Push delivery not configured'),
            value: true,
            onChanged: (_) {},
          ),
          const ListTile(title: Text('Privacy'), subtitle: Text('Faculty data used only for assessment workflows.')),
          ListTile(
            title: const Text('Help & Support'),
            onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Contact your institution IT office.'))),
          ),
          ListTile(
            title: const Text('About FacultyLink'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.push(context, MaterialPageRoute<void>(builder: (_) => const AboutScreen())),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text('Logout', style: TextStyle(color: Colors.red)),
            onTap: () {
              Navigator.of(context).pushNamedAndRemoveUntil(WelcomeScreen.routeName, (_) => false);
            },
          ),
        ],
      ),
    );
  }

  void _showChangePassword(BuildContext context) {
    final current = TextEditingController();
    final next = TextEditingController();
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) {
        return Padding(
          padding: EdgeInsets.only(left: 20, right: 20, top: 20, bottom: 20 + MediaQuery.viewInsetsOf(ctx).bottom),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              FlTextField(label: 'Current password', controller: current, obscureText: true),
              const SizedBox(height: 12),
              FlTextField(label: 'New password', controller: next, obscureText: true),
              const SizedBox(height: 16),
              FlPrimaryButton(
                label: 'Save (mock)',
                onPressed: () async {
                  try {
                    await FacultyApi.changePassword();
                  } catch (_) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Password change not saved — Flask API not connected.')),
                      );
                    }
                  }
                  if (ctx.mounted) Navigator.pop(ctx);
                },
              ),
            ],
          ),
        );
      },
    );
  }
}
