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
      brightness: Brightness.light,
    );
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
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
      drawerTheme: const DrawerThemeData(backgroundColor: forest),
      appBarTheme: const AppBarTheme(
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

  // Dark palette kutoka base.css [data-theme=dark]
  static const Color darkPrimary = Color(0xFF4CAF75);
  static const Color darkPrimaryHover = Color(0xFF6FC890);
  static const Color darkPaper = Color(0xFF101412);
  static const Color darkCard = Color(0xFF1A211D);
  static const Color darkSurfaceMuted = Color(0xFF232B26);
  static const Color darkInk = Color(0xFFEEF3EF);
  static const Color darkMuted = Color(0xFFA7B5AC);
  static const Color darkTitle = Color(0xFFA8D5B5);
  static const Color darkBorder = Color(0xFF334038);
  static const Color darkForest = Color(0xFF0D1411);
  static const Color darkNav = Color(0xFF121916);

  static ThemeData dark() {
    final base = ColorScheme.fromSeed(
      seedColor: darkPrimary,
      primary: darkPrimary,
      surface: darkPaper,
      brightness: Brightness.dark,
    );
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      fontFamily: uiFont,
      colorScheme: base.copyWith(
        primary: darkPrimary,
        onPrimary: Colors.white,
        secondary: goldEdge,
        surface: darkPaper,
        error: const Color(0xFFEF5350),
        onSurface: darkInk,
      ),
      scaffoldBackgroundColor: darkPaper,
      drawerTheme: const DrawerThemeData(backgroundColor: darkForest),
      appBarTheme: const AppBarTheme(
        backgroundColor: darkNav,
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
      dividerColor: darkBorder,
      cardTheme: CardThemeData(
        color: darkCard,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: darkBorder),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: darkSurfaceMuted,
        contentPadding: const EdgeInsets.symmetric(horizontal: 15, vertical: 14),
        hintStyle: const TextStyle(color: darkMuted),
        labelStyle: const TextStyle(color: darkMuted),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: darkBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: darkBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: darkPrimary, width: 2),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: darkPrimary,
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
