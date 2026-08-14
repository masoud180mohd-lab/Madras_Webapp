import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../auth/view_models/auth_view_model.dart';
import '../view_models/classes_view_model.dart';

class ClassesView extends StatefulWidget {
  const ClassesView({
    super.key,
    required this.auth,
    required this.viewModel,
  });

  final AuthViewModel auth;
  final ClassesViewModel viewModel;

  @override
  State<ClassesView> createState() => _ClassesViewState();
}

class _ClassesViewState extends State<ClassesView> {
  @override
  void initState() {
    super.initState();
    widget.viewModel.load();
  }

  @override
  Widget build(BuildContext context) {
    final profile = widget.auth.profile;
    return Scaffold(
      appBar: AppBar(
        title: const Text(MadrasaCopy.brand),
        actions: [
          IconButton(
            tooltip: MadrasaCopy.logout,
            onPressed: () => widget.auth.logout(),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: ListenableBuilder(
        listenable: widget.viewModel,
        builder: (context, _) {
          if (widget.viewModel.loading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (widget.viewModel.error != null) {
            return _Message(
              text: widget.viewModel.error!,
              onRetry: widget.viewModel.load,
            );
          }
          final items = widget.viewModel.madarasa;
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
            children: [
              _WelcomeBanner(
                jina: profile?.jina,
                cheo: profile?.cheo,
              ),
              const SizedBox(height: 20),
              const _SectionHeader(title: MadrasaCopy.classes),
              const SizedBox(height: 16),
              if (items.isEmpty)
                const _EmptyCard(text: MadrasaCopy.emptyClasses)
              else
                ...items.map(
                  (darasa) => Padding(
                    padding: const EdgeInsets.only(bottom: 14),
                    child: _ClassCard(
                      jina: darasa.jina,
                      maelezo: darasa.maelezo,
                      onTap: () => context.push(
                        '/madarasa/${darasa.id}',
                        extra: darasa,
                      ),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _WelcomeBanner extends StatelessWidget {
  const _WelcomeBanner({this.jina, this.cheo});

  final String? jina;
  final String? cheo;

  @override
  Widget build(BuildContext context) {
    return AccentCard(
      accent: MadrasaTheme.gold,
      padding: const EdgeInsets.all(18),
      child: Row(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: MadrasaTheme.surfaceMuted,
              border: Border.all(color: MadrasaTheme.goldEdge, width: 2),
            ),
            clipBehavior: Clip.antiAlias,
            child: Image.asset(
              'assets/images/logo.png',
              fit: BoxFit.cover,
              errorBuilder: (context, error, stack) => const Icon(
                Icons.mosque,
                color: MadrasaTheme.primary,
                size: 28,
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
                    letterSpacing: 0.4,
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
                if (cheo != null && cheo!.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  _RoleBadge(cheo: cheo!),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _RoleBadge extends StatelessWidget {
  const _RoleBadge({required this.cheo});

  final String cheo;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: MadrasaTheme.successBg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: MadrasaTheme.successBorder),
      ),
      child: Text(
        cheo,
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: MadrasaTheme.successText,
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.only(bottom: 10),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(color: MadrasaTheme.underlineGold, width: 2),
        ),
      ),
      child: Row(
        children: [
          const Icon(Icons.school, color: MadrasaTheme.primary, size: 22),
          const SizedBox(width: 10),
          Text(
            title,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: MadrasaTheme.primary,
            ),
          ),
        ],
      ),
    );
  }
}

class _ClassCard extends StatelessWidget {
  const _ClassCard({
    required this.jina,
    required this.maelezo,
    required this.onTap,
  });

  final String jina;
  final String? maelezo;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return AccentCard(
      onTap: onTap,
      padding: const EdgeInsets.fromLTRB(18, 18, 12, 18),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  jina,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: MadrasaTheme.primaryHover,
                  ),
                ),
                if (maelezo != null && maelezo!.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    maelezo!,
                    style: const TextStyle(
                      fontSize: 14,
                      color: MadrasaTheme.muted,
                    ),
                  ),
                ],
              ],
            ),
          ),
          const Icon(Icons.chevron_right, color: MadrasaTheme.muted),
        ],
      ),
    );
  }
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(40),
      decoration: BoxDecoration(
        color: MadrasaTheme.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: MadrasaTheme.border,
          width: 2,
          style: BorderStyle.solid,
        ),
      ),
      child: Column(
        children: [
          const Icon(Icons.inbox_outlined, color: MadrasaTheme.faint, size: 40),
          const SizedBox(height: 12),
          Text(
            text,
            textAlign: TextAlign.center,
            style: const TextStyle(color: MadrasaTheme.muted),
          ),
        ],
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({required this.text, this.onRetry});

  final String text;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(text, textAlign: TextAlign.center),
            if (onRetry != null) ...[
              const SizedBox(height: 12),
              FilledButton(
                onPressed: onRetry,
                child: const Text(MadrasaCopy.retry),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
