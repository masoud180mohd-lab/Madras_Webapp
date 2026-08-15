import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/theme_controller.dart';
import '../../../core/widgets/accent_card.dart';
import '../../auth/view_models/auth_view_model.dart';

class SettingsView extends StatelessWidget {
  const SettingsView({super.key, required this.auth});

  final AuthViewModel auth;

  @override
  Widget build(BuildContext context) {
    final theme = context.watch<ThemeController>();
    final profile = auth.profile;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        if (profile != null)
          AccentCard(
            accent: MadrasaTheme.gold,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  profile.jina,
                  style: const TextStyle(
                    fontFamily: MadrasaTheme.brandFont,
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: MadrasaTheme.title,
                  ),
                ),
                if (profile.cheo != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    profile.cheo!,
                    style: const TextStyle(color: MadrasaTheme.muted),
                  ),
                ],
              ],
            ),
          ),
        const SizedBox(height: 16),
        AccentCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                MadrasaCopy.appearance,
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: MadrasaTheme.primary,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 8),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(
                  theme.isDark
                      ? MadrasaCopy.darkMode
                      : MadrasaCopy.lightMode,
                ),
                subtitle: Text(
                  theme.isDark
                      ? 'Muonekano wa giza (kama wavuti)'
                      : 'Muonekano wa kawaida',
                ),
                value: theme.isDark,
                activeThumbColor: MadrasaTheme.primary,
                onChanged: (value) {
                  theme.setMode(value ? ThemeMode.dark : ThemeMode.light);
                },
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        AccentCard(
          child: ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.logout, color: MadrasaTheme.danger),
            title: const Text(
              MadrasaCopy.logout,
              style: TextStyle(
                color: MadrasaTheme.danger,
                fontWeight: FontWeight.w700,
              ),
            ),
            subtitle: const Text('Toka kwenye akaunti yako'),
            onTap: () => auth.logout(),
          ),
        ),
      ],
    );
  }
}
