import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../../core/widgets/student_stat_cards.dart';

class ClassHubView extends StatefulWidget {
  const ClassHubView({
    super.key,
    required this.darasa,
    required this.canTakeAttendance,
    required this.canViewStudents,
    this.catalog,
  });

  final Darasa darasa;
  final bool canTakeAttendance;
  final bool canViewStudents;
  final CatalogRepository? catalog;

  @override
  State<ClassHubView> createState() => _ClassHubViewState();
}

class _ClassHubViewState extends State<ClassHubView> {
  int? _wavulana;
  int? _wasichana;
  int? _jumla;

  @override
  void initState() {
    super.initState();
    _wavulana = widget.darasa.wavulana;
    _wasichana = widget.darasa.wasichana;
    _jumla = widget.darasa.idadiWanafunzi;
    _loadCountsIfNeeded();
  }

  @override
  void didUpdateWidget(covariant ClassHubView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.darasa.id != widget.darasa.id) {
      _wavulana = widget.darasa.wavulana;
      _wasichana = widget.darasa.wasichana;
      _jumla = widget.darasa.idadiWanafunzi;
      _loadCountsIfNeeded();
    }
  }

  Future<void> _loadCountsIfNeeded() async {
    final repo = widget.catalog;
    if (repo == null) {
      return;
    }
    try {
      final rows = await repo.wanafunzi(darasa: '${widget.darasa.id}');
      if (!mounted) {
        return;
      }
      final me = rows.where((r) => r.badge == 'ME').length;
      final ke = rows.where((r) => r.badge == 'KE').length;
      setState(() {
        _wavulana = me;
        _wasichana = ke;
        _jumla = rows.length;
      });
    } catch (_) {
      // Keep initial darasa counts if network fetch fails
    }
  }

  @override
  Widget build(BuildContext context) {
    final wavulana = _wavulana ?? 0;
    final wasichana = _wasichana ?? 0;
    final jumla = _jumla ?? (wavulana + wasichana);

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        Text(
          widget.darasa.jina,
          style: const TextStyle(
            fontFamily: MadrasaTheme.brandFont,
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: MadrasaTheme.title,
          ),
        ),
        if (widget.darasa.maelezo != null &&
            widget.darasa.maelezo!.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            widget.darasa.maelezo!,
            style: const TextStyle(color: MadrasaTheme.muted),
          ),
        ],
        const SizedBox(height: 16),
        StudentStatCards(
          wavulana: wavulana,
          wasichana: wasichana,
          jumla: jumla,
        ),
        const SizedBox(height: 20),
        if (widget.canTakeAttendance || widget.canViewStudents)
          _HubCard(
            title: MadrasaCopy.rollCall,
            hint: widget.canTakeAttendance
                ? 'Rekodi yupo / hayupo'
                : MadrasaCopy.viewOnly,
            watermarkIcon: Icons.fact_check_rounded,
            onTap: () =>
                context.push('/madarasa/${widget.darasa.id}/mahudhurio'),
          ),
        if (widget.canViewStudents)
          _HubCard(
            title: MadrasaCopy.classStudents,
            hint: '$jumla wanafunzi (Wanaume: $wavulana · Wanawake: $wasichana)',
            watermarkIcon: Icons.groups_rounded,
            onTap: () => context.push('/wanafunzi?darasa=${widget.darasa.id}'),
          ),
      ],
    );
  }
}

class _HubCard extends StatelessWidget {
  const _HubCard({
    required this.title,
    required this.hint,
    required this.watermarkIcon,
    required this.onTap,
  });

  final String title;
  final String hint;
  final IconData watermarkIcon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AccentCard(
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
                  color: MadrasaTheme.primary.withValues(alpha: 0.08),
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
