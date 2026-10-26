import 'package:flutter/material.dart';

import '../theme.dart';
import 'accent_card.dart';

class HubCard extends StatelessWidget {
  const HubCard({
    super.key,
    required this.title,
    required this.hint,
    required this.watermarkIcon,
    required this.onTap,
    this.accent,
  });

  final String title;
  final String hint;
  final IconData watermarkIcon;
  final VoidCallback onTap;
  final Color? accent;

  @override
  Widget build(BuildContext context) {
    final effectiveAccent = accent ?? MadrasaTheme.primary;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AccentCard(
        accent: effectiveAccent,
        onTap: onTap,
        padding: EdgeInsets.zero,
        child: Stack(
          children: [
            Positioned(
              right: 28,
              bottom: -10,
              child: IgnorePointer(
                child: Icon(
                  watermarkIcon,
                  size: 64,
                  color: effectiveAccent.withValues(alpha: 0.08),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 18, 12, 18),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w700,
                            color: MadrasaTheme.primaryHover,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          hint,
                          style: const TextStyle(color: MadrasaTheme.muted),
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.chevron_right, color: MadrasaTheme.muted),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
