import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../data/models/models.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';

class ClassHubView extends StatelessWidget {
  const ClassHubView({
    super.key,
    required this.darasa,
    required this.canTakeAttendance,
    required this.canViewStudents,
  });

  final Darasa darasa;
  final bool canTakeAttendance;
  final bool canViewStudents;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        Text(
          darasa.jina,
          style: const TextStyle(
            fontFamily: MadrasaTheme.brandFont,
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: MadrasaTheme.title,
          ),
        ),
        if (darasa.maelezo != null && darasa.maelezo!.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            darasa.maelezo!,
            style: const TextStyle(color: MadrasaTheme.muted),
          ),
        ],
        const SizedBox(height: 20),
        if (canTakeAttendance || canViewStudents)
          _HubCard(
            title: MadrasaCopy.rollCall,
            hint: canTakeAttendance
                ? 'Rekodi yupo / hayupo'
                : MadrasaCopy.viewOnly,
            onTap: () => context.push('/madarasa/${darasa.id}/mahudhurio'),
          ),
        if (canViewStudents)
          _HubCard(
            title: MadrasaCopy.classStudents,
            hint: darasa.idadiWanafunzi == null
                ? 'Orodha ya wanafunzi hai'
                : '${darasa.idadiWanafunzi} wanafunzi',
            onTap: () => context.push('/wanafunzi?darasa=${darasa.id}'),
          ),
      ],
    );
  }
}

class _HubCard extends StatelessWidget {
  const _HubCard({
    required this.title,
    required this.hint,
    required this.onTap,
  });

  final String title;
  final String hint;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AccentCard(
        onTap: onTap,
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
    );
  }
}
