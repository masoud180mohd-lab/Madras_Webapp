import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../data/services/api_client.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../../core/widgets/authenticated_photo.dart';
import '../view_models/catalog_view_model.dart';

class CatalogListView extends StatefulWidget {
  const CatalogListView({
    super.key,
    required this.viewModel,
    this.hint,
    this.searchable = false,
    this.onSearch,
  });

  final CatalogViewModel viewModel;
  final String? hint;
  final bool searchable;
  final ValueChanged<String>? onSearch;

  @override
  State<CatalogListView> createState() => _CatalogListViewState();
}

class _CatalogListViewState extends State<CatalogListView> {
  final _search = TextEditingController();

  @override
  void initState() {
    super.initState();
    widget.viewModel.load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<ApiClient>();
    return ListenableBuilder(
      listenable: widget.viewModel,
      builder: (context, _) {
        final vm = widget.viewModel;
        if (vm.loading && vm.rows.isEmpty) {
          return const Center(child: CircularProgressIndicator());
        }
        if (vm.error != null && vm.rows.isEmpty) {
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
        return ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          children: [
            if (widget.hint != null) ...[
              Text(
                widget.hint!,
                style: const TextStyle(color: MadrasaTheme.muted, fontSize: 14),
              ),
              const SizedBox(height: 12),
            ],
            if (widget.searchable) ...[
              TextField(
                controller: _search,
                decoration: const InputDecoration(
                  hintText: MadrasaCopy.search,
                  prefixIcon: Icon(Icons.search),
                ),
                onSubmitted: (value) {
                  widget.onSearch?.call(value);
                  widget.viewModel.load(q: value);
                },
              ),
              const SizedBox(height: 16),
            ],
            if (vm.rows.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 40),
                child: Text(
                  MadrasaCopy.emptyList,
                  textAlign: TextAlign.center,
                  style: TextStyle(color: MadrasaTheme.muted),
                ),
              )
            else
              ...vm.rows.map((row) {
                if (row.isHeader) {
                  return Padding(
                    padding: const EdgeInsets.fromLTRB(0, 12, 0, 10),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          row.title,
                          style: const TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w800,
                            color: MadrasaTheme.primary,
                          ),
                        ),
                        if (row.subtitle != null)
                          Text(
                            row.subtitle!,
                            style: const TextStyle(
                              color: MadrasaTheme.muted,
                              fontSize: 13,
                            ),
                          ),
                      ],
                    ),
                  );
                }
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: AccentCard(
                    onTap: row.detailPath == null
                        ? null
                        : () => context.push(row.detailPath!),
                    padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
                    child: Row(
                      children: [
                        if (row.photoUrl != null || row.detailPath != null)
                          Padding(
                            padding: const EdgeInsets.only(right: 12),
                            child: AuthenticatedPhoto(
                              api: api,
                              url: row.photoUrl,
                              fallbackLabel: row.title,
                              radius: 24,
                            ),
                          ),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                row.title,
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                  color: MadrasaTheme.title,
                                ),
                              ),
                              if (row.subtitle != null &&
                                  row.subtitle!.isNotEmpty) ...[
                                const SizedBox(height: 4),
                                Text(
                                  row.subtitle!,
                                  style: const TextStyle(
                                    color: MadrasaTheme.muted,
                                    fontSize: 13,
                                  ),
                                ),
                              ],
                              if (row.badge != null) ...[
                                const SizedBox(height: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 10,
                                    vertical: 3,
                                  ),
                                  decoration: BoxDecoration(
                                    color: MadrasaTheme.successBg,
                                    borderRadius: BorderRadius.circular(999),
                                    border: Border.all(
                                      color: MadrasaTheme.successBorder,
                                    ),
                                  ),
                                  child: Text(
                                    row.badge!,
                                    style: const TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.w700,
                                      color: MadrasaTheme.successText,
                                    ),
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                        if (row.trailing != null && row.trailing!.isNotEmpty)
                          Text(
                            row.trailing!,
                            style: const TextStyle(
                              color: MadrasaTheme.gold,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        if (row.detailPath != null)
                          const Icon(
                            Icons.chevron_right,
                            color: MadrasaTheme.muted,
                          ),
                      ],
                    ),
                  ),
                );
              }),
          ],
        );
      },
    );
  }
}
