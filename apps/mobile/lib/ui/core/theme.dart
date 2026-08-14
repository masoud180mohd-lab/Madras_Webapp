import 'package:flutter/material.dart';

/// Rangi na mitindo hii inalingana moja kwa moja na `usimamizi/static/usimamizi/css/base.css`
/// ya web app, ili muonekano wa simu ufanane na tovuti.
class MadrasaTheme {
  // Palette ya msingi (light) kutoka base.css :root
  static const Color primary = Color(0xFF1F6B45); // --primary
  static const Color primaryHover = Color(0xFF155536); // --primary-hover
  static const Color secondary = Color(0xFF0B6E8F); // --secondary
  static const Color forest = Color(0xFF143D2A); // --sidebar-bg / --title-color
  static const Color gold = Color(0xFFB8893D); // --accent
  static const Color goldEdge = Color(0xFFD4A84B); // --sidebar-edge
  static const Color underlineGold = Color(0xFFFFD700); // kichwa cha orodha

  static const Color paper = Color(0xFFEEF3EF); // --bg-body
  static const Color card = Color(0xFFFFFFFF); // --card-bg
  static const Color surfaceMuted = Color(0xFFF4F7F5); // --surface-muted
  static const Color hover = Color(0xFFE8F0EA); // --hover-bg

  static const Color ink = Color(0xFF1C2B24); // --text-main
  static const Color muted = Color(0xFF5F6F66); // --text-muted
  static const Color faint = Color(0xFF7A8A82); // --text-faint
  static const Color title = Color(0xFF143D2A); // --title-color

  static const Color border = Color(0xFFD5E0D8); // --border-color
  static const Color focusRing = Color(0x381F6B45); // --focus-ring ~22%

  static const Color danger = Color(0xFFC0392B); // --danger
  static const Color dangerBg = Color(0xFFFDE8E8); // --danger-bg
  static const Color dangerText = Color(0xFFC62828); // --danger-text
  static const Color dangerBorder = Color(0xFFF8B4B4); // --danger-border

  static const Color successBg = Color(0xFFE8F5E9); // --success-bg
  static const Color successText = Color(0xFF1B5E20); // --success-text
  static const Color successBorder = Color(0xFFA5D6A7); // --success-border

  static const Color female = Color(0xFFA8325E); // --female

  // Fonti zinazolingana na web: "Source Sans 3" (UI) na "Amiri" (brand).
  static const String uiFont = 'SourceSans3';
  static const String brandFont = 'Amiri';

  static ThemeData light() {
    final base = ColorScheme.fromSeed(
      seedColor: primary,
      primary: primary,
      surface: paper,
    );
    return ThemeData(
      useMaterial3: true,
      fontFamily: uiFont,
      colorScheme: base.copyWith(
        primary: primary,
        onPrimary: Colors.white,
        secondary: gold,
        surface: paper,
        error: danger,
        onSurface: ink,
      ),
      scaffoldBackgroundColor: paper,
      appBarTheme: const AppBarTheme(
        // Web .header hutumia --nav-bg (#1F6B45)
        backgroundColor: primary,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: Colors.white,
          fontFamily: brandFont,
          fontSize: 21,
          fontWeight: FontWeight.w700,
        ),
      ),
      dividerColor: border,
      cardTheme: CardThemeData(
        color: card,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: border),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 15, vertical: 14),
        hintStyle: const TextStyle(color: muted),
        labelStyle: const TextStyle(color: muted),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: primary, width: 2),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(50),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
    );
  }
}
