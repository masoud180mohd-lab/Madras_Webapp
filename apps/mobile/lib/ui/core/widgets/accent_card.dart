import 'package:flutter/material.dart';

import '../theme.dart';

/// Kadi nyeupe yenye upau wa rangi upande wa kushoto (kama `.orodha_madarasa-card`
/// ya web). Tunatumia upau halisi badala ya mpaka wa rangi mchanganyiko kwa
/// sababu Flutter hairuhusu `Border` ya rangi tofauti pamoja na `borderRadius`.
class AccentCard extends StatelessWidget {
  const AccentCard({
    super.key,
    required this.child,
    this.accent = MadrasaTheme.primary,
    this.accentWidth = 6,
    this.padding = const EdgeInsets.all(16),
    this.onTap,
  });

  final Widget child;
  final Color accent;
  final double accentWidth;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final content = IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(width: accentWidth, color: accent),
          Expanded(
            child: Padding(padding: padding, child: child),
          ),
        ],
      ),
    );

    return DecoratedBox(
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color ??
            (Theme.of(context).brightness == Brightness.dark
                ? MadrasaTheme.darkCard
                : MadrasaTheme.card),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Theme.of(context).brightness == Brightness.dark
              ? MadrasaTheme.darkBorder
              : MadrasaTheme.border,
        ),
        boxShadow: [
          BoxShadow(
            color: Theme.of(context).brightness == Brightness.dark
                ? const Color(0x66000000)
                : const Color(0x14143D2A),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: onTap == null
            ? content
            : Material(
                color: Colors.transparent,
                child: InkWell(onTap: onTap, child: content),
              ),
      ),
    );
  }
}

/// Kadi yenye upau wa rangi juu (kama `.login-card` yenye `border-top: 6px`).
class TopAccentCard extends StatelessWidget {
  const TopAccentCard({
    super.key,
    required this.child,
    this.accent = MadrasaTheme.primary,
    this.accentHeight = 6,
    this.radius = 16,
    this.padding = const EdgeInsets.all(40),
  });

  final Widget child;
  final Color accent;
  final double accentHeight;
  final double radius;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: dark ? MadrasaTheme.darkCard : MadrasaTheme.card,
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(
          color: dark ? MadrasaTheme.darkBorder : MadrasaTheme.border,
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0x14000000),
            blurRadius: 30,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(height: accentHeight, color: accent),
            Padding(padding: padding, child: child),
          ],
        ),
      ),
    );
  }
}
