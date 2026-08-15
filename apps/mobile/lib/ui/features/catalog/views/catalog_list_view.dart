import 'package:flutter/material.dart';

import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
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
              ...vm.rows.map(
                (row) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: AccentCard(
                    padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
                    child: Row(
                      children: [
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
                      ],
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
