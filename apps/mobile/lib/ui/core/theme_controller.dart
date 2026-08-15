import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeController extends ChangeNotifier {
  ThemeController();

  static const _key = 'madrasa_theme_mode';

  ThemeMode _mode = ThemeMode.light;
  bool _ready = false;

  ThemeMode get mode => _mode;
  bool get ready => _ready;
  bool get isDark => _mode == ThemeMode.dark;

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == 'dark') {
      _mode = ThemeMode.dark;
    } else if (raw == 'light') {
      _mode = ThemeMode.light;
    }
    _ready = true;
    notifyListeners();
  }

  Future<void> setMode(ThemeMode mode) async {
    if (_mode == mode) {
      return;
    }
    _mode = mode;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _key,
      mode == ThemeMode.dark ? 'dark' : 'light',
    );
  }

  Future<void> toggle() {
    return setMode(isDark ? ThemeMode.light : ThemeMode.dark);
  }
}
