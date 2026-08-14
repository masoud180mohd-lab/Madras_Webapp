import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/copy.dart';
import '../../core/theme.dart';
import '../view_models/auth_view_model.dart';
import '../../classes/view_models/classes_view_model.dart';

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
        title: const Text(MadrasaCopy.classes),
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
          if (items.isEmpty) {
            return const _Message(text: MadrasaCopy.emptyClasses);
          }
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                child: Text(
                  profile == null
                      ? MadrasaCopy.brand
                      : '${profile.jina}${profile.cheo == null ? '' : ' · ${profile.cheo}'}',
                  style: const TextStyle(
                    color: MadrasaTheme.muted,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Expanded(
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                  itemCount: items.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final darasa = items[index];
                    return Material(
                      color: MadrasaTheme.card,
                      borderRadius: BorderRadius.circular(12),
                      child: ListTile(
                        title: Text(
                          darasa.jina,
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                        subtitle: darasa.maelezo == null || darasa.maelezo!.isEmpty
                            ? null
                            : Text(darasa.maelezo!),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => context.push(
                          '/madarasa/${darasa.id}',
                          extra: darasa,
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          );
        },
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
