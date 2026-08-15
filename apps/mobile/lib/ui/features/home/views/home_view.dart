import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../auth/view_models/auth_view_model.dart';
import '../../catalog/view_models/catalog_view_model.dart';

class HomeView extends StatefulWidget {
  const HomeView({
    super.key,
    required this.auth,
    required this.viewModel,
  });

  final AuthViewModel auth;
  final DashboardViewModel viewModel;

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  @override
  void initState() {
    super.initState();
    widget.viewModel.load();
  }

  @override
  Widget build(BuildContext context) {
    final profile = widget.auth.profile;
    return ListenableBuilder(
      listenable: widget.viewModel,
      builder: (context, _) {
        final vm = widget.viewModel;
        if (vm.loading && vm.data == null) {
          return const Center(child: CircularProgressIndicator());
        }
        if (vm.error != null && vm.data == null) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(vm.error!, textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  FilledButton(
                    onPressed: vm.load,
                    child: const Text(MadrasaCopy.retry),
                  ),
                ],
              ),
            ),
          );
        }
        final data = vm.data;
        final jina = data?.jina ?? profile?.jina;
        final cheo = data?.cheo ?? profile?.cheo;
        return ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          children: [
            AccentCard(
              accent: MadrasaTheme.gold,
              padding: const EdgeInsets.all(18),
              child: Row(
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: MadrasaTheme.goldEdge, width: 2),
                    ),
                    clipBehavior: Clip.antiAlias,
                    child: Image.asset(
                      'assets/images/logo.png',
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stack) => const Icon(
                        Icons.mosque,
                        color: MadrasaTheme.primary,
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Al-Madrasatul Rasulillah · Mwera',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: MadrasaTheme.gold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          jina == null ? 'Karibu' : 'Karibu, $jina',
                          style: const TextStyle(
                            fontFamily: MadrasaTheme.brandFont,
                            fontSize: 22,
                            fontWeight: FontWeight.w700,
                            color: MadrasaTheme.title,
                          ),
                        ),
                        if (cheo != null && cheo.isNotEmpty) ...[
                          const SizedBox(height: 6),
                          Text(
                            cheo,
                            style: const TextStyle(
                              color: MadrasaTheme.successText,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            if (data != null && data.vipimo.isNotEmpty) ...[
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  for (final metric in data.vipimo)
                    SizedBox(
                      width: 160,
                      child: AccentCard(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              metric.label,
                              style: const TextStyle(
                                color: MadrasaTheme.muted,
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              metric.value,
                              style: TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.w800,
                                color: metric.tone == 'warning'
                                    ? MadrasaTheme.gold
                                    : MadrasaTheme.title,
                              ),
                            ),
                            if (metric.hint != null && metric.hint!.isNotEmpty)
                              Text(
                                metric.hint!,
                                style: const TextStyle(
                                  color: MadrasaTheme.faint,
                                  fontSize: 12,
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 20),
            ],
            if (profile?.canViewDirectory == true ||
                profile?.canViewStudents == true)
              _QuickLink(
                label: MadrasaCopy.classes,
                hint: 'Mahudhurio na orodha',
                onTap: () => context.go('/madarasa'),
              ),
            if (profile?.canTakeAttendance == true ||
                profile?.canViewStudents == true)
              _QuickLink(
                label: MadrasaCopy.absentees,
                hint: 'Ufuatiliaji wa mahudhurio',
                onTap: () => context.go('/watoro'),
              ),
            if (data != null && data.matangazo.isNotEmpty) ...[
              const SizedBox(height: 8),
              const Text(
                'Matangazo',
                style: TextStyle(
                  fontWeight: FontWeight.w700,
                  color: MadrasaTheme.primary,
                  fontSize: 18,
                ),
              ),
              const SizedBox(height: 10),
              for (final item in data.matangazo)
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: AccentCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.title,
                          style: const TextStyle(
                            fontWeight: FontWeight.w700,
                            color: MadrasaTheme.title,
                          ),
                        ),
                        if (item.subtitle != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            item.subtitle!,
                            style: const TextStyle(color: MadrasaTheme.muted),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
            ],
          ],
        );
      },
    );
  }
}

class _QuickLink extends StatelessWidget {
  const _QuickLink({
    required this.label,
    required this.hint,
    required this.onTap,
  });

  final String label;
  final String hint;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: AccentCard(
        onTap: onTap,
        padding: const EdgeInsets.fromLTRB(16, 14, 12, 14),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      color: MadrasaTheme.primaryHover,
                    ),
                  ),
                  Text(
                    hint,
                    style: const TextStyle(
                      color: MadrasaTheme.muted,
                      fontSize: 13,
                    ),
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
