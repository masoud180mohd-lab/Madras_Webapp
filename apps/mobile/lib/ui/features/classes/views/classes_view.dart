import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../view_models/classes_view_model.dart';

class ClassesView extends StatefulWidget {
  const ClassesView({
    super.key,
    required this.viewModel,
  });

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
    return ListenableBuilder(
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
