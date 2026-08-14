import 'package:flutter/material.dart';

class MadrasaTheme {
  static const Color primary = Color(0xFF1F6B45);
  static const Color forest = Color(0xFF143D2A);
  static const Color gold = Color(0xFFB8893D);
  static const Color paper = Color(0xFFEEF3EF);
  static const Color ink = Color(0xFF1C2B24);
  static const Color muted = Color(0xFF5F6F66);
  static const Color danger = Color(0xFFC0392B);
  static const Color card = Color(0xFFFFFFFF);

  static ThemeData light() {
    final base = ColorScheme.fromSeed(
      seedColor: primary,
      primary: primary,
      surface: paper,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: base.copyWith(
        primary: primary,
        onPrimary: Colors.white,
        secondary: gold,
        surface: paper,
        error: danger,
      ),
      scaffoldBackgroundColor: paper,
      appBarTheme: const AppBarTheme(
        backgroundColor: forest,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: primary, width: 2),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
    );
  }
}
