import 'package:flutter/material.dart';

import '../copy.dart';
import '../theme.dart';

/// Kadi 3 za takwimu za wanafunzi (Wanaume, Wanawake, Jumla) zenye watermark
/// inayobadilika kulingana na idadi ya darasa au orodha husika.
class StudentStatCards extends StatelessWidget {
  const StudentStatCards({
    super.key,
    required this.wavulana,
    required this.wasichana,
    required this.jumla,
    this.selectedGender,
    this.onSelectGender,
  });

  final int wavulana;
  final int wasichana;
  final int jumla;
  final String? selectedGender;
  final ValueChanged<String?>? onSelectGender;

  static const Color maleColor = Color(0xFF0288D1);
  static const Color femaleColor = Color(0xFFC2185B);
  static const Color totalColor = MadrasaTheme.primary;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _WatermarkStatCard(
            label: MadrasaCopy.maleStudents,
            value: wavulana,
            accent: maleColor,
            watermarkIcon: Icons.male_rounded,
            selected: selectedGender == 'ME',
            onTap: onSelectGender == null
                ? null
                : () => onSelectGender!(
                      selectedGender == 'ME' ? null : 'ME',
                    ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _WatermarkStatCard(
            label: MadrasaCopy.femaleStudents,
            value: wasichana,
            accent: femaleColor,
            watermarkIcon: Icons.female_rounded,
            selected: selectedGender == 'KE',
            onTap: onSelectGender == null
                ? null
                : () => onSelectGender!(
                      selectedGender == 'KE' ? null : 'KE',
                    ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _WatermarkStatCard(
            label: MadrasaCopy.totalStudents,
            value: jumla,
            accent: totalColor,
            watermarkIcon: Icons.groups_rounded,
            selected: onSelectGender != null && selectedGender == null,
            onTap: onSelectGender == null ? null : () => onSelectGender!(null),
          ),
        ),
      ],
    );
  }
}

class _WatermarkStatCard extends StatelessWidget {
  const _WatermarkStatCard({
    required this.label,
    required this.value,
    required this.accent,
    required this.watermarkIcon,
    this.selected = false,
    this.onTap,
  });

  final String label;
  final int value;
  final Color accent;
  final IconData watermarkIcon;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = selected
        ? accent.withValues(alpha: dark ? 0.22 : 0.09)
        : (dark ? MadrasaTheme.darkCard : MadrasaTheme.card);
    final borderColor = selected
        ? accent.withValues(alpha: 0.65)
        : (dark ? MadrasaTheme.darkBorder : MadrasaTheme.border);

    return DecoratedBox(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor, width: selected ? 1.6 : 1.0),
        boxShadow: [
          BoxShadow(
            color: dark
                ? const Color(0x55000000)
                : accent.withValues(alpha: 0.08),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: onTap,
            child: Stack(
              children: [
                // Top accent bar
                Positioned(
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 4.5,
                  child: ColoredBox(color: accent),
                ),
                // Dynamic watermark number in background
                Positioned(
                  right: 34,
                  bottom: -8,
                  child: IgnorePointer(
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 280),
                      child: Text(
                        '$value',
                        key: ValueKey<int>(value),
                        style: TextStyle(
                          fontSize: 44,
                          fontWeight: FontWeight.w900,
                          height: 1,
                          color: accent.withValues(alpha: dark ? 0.10 : 0.07),
                        ),
                      ),
                    ),
                  ),
                ),
                // Watermark icon in bottom-right corner
                Positioned(
                  right: -8,
                  bottom: -8,
                  child: IgnorePointer(
                    child: Icon(
                      watermarkIcon,
                      size: 56,
                      color: accent.withValues(alpha: dark ? 0.18 : 0.13),
                    ),
                  ),
                ),
                // Foreground content
                Padding(
                  padding: const EdgeInsets.fromLTRB(12, 14, 12, 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        label,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: dark ? MadrasaTheme.darkMuted : MadrasaTheme.muted,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.3,
                        ),
                      ),
                      const SizedBox(height: 6),
                      TweenAnimationBuilder<int>(
                        tween: IntTween(begin: 0, end: value),
                        duration: const Duration(milliseconds: 320),
                        builder: (context, animatedValue, _) {
                          return Text(
                            '$animatedValue',
                            style: TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.w900,
                              color: accent,
                              height: 1.05,
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
