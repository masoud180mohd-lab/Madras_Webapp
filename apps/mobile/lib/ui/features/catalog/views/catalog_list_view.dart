import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../data/models/models.dart';
import '../../../../data/services/api_client.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../../core/widgets/authenticated_photo.dart';
import '../../../core/widgets/student_stat_cards.dart';
import '../view_models/catalog_view_model.dart';

class CatalogListView extends StatefulWidget {
  const CatalogListView({
    super.key,
    required this.viewModel,
    this.hint,
    this.searchable = false,
    this.showStudentStats = false,
    this.onSearch,
    this.topBar,
    this.onRowTap,
  });

  final CatalogViewModel viewModel;
  final String? hint;
  final bool searchable;
  final bool showStudentStats;
  final ValueChanged<String>? onSearch;
  final Widget Function(BuildContext context, VoidCallback reload)? topBar;
  final Future<void> Function(
    BuildContext context,
    CatalogRow row,
    VoidCallback reload,
  )? onRowTap;

  @override
  State<CatalogListView> createState() => _CatalogListViewState();
}

class _CatalogListViewState extends State<CatalogListView> {
  final _search = TextEditingController();
  String? _selectedGender;

  @override
  void initState() {
    super.initState();
    widget.viewModel.load();
  }

  @override
  void didUpdateWidget(covariant CatalogListView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.viewModel != widget.viewModel) {
      widget.viewModel.load(q: _search.text.trim().isEmpty ? null : _search.text.trim());
    }
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

        final allRows = vm.rows;
        final wavulanaCount = allRows.where((r) => r.badge == 'ME').length;
        final wasichanaCount = allRows.where((r) => r.badge == 'KE').length;
        final jumlaCount = (wavulanaCount + wasichanaCount) > 0
            ? (wavulanaCount + wasichanaCount)
            : allRows.where((r) => !r.isHeader).length;

        final filteredRows = _selectedGender == null
            ? allRows
            : allRows.where((r) => r.badge == _selectedGender).toList();

        return ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          children: [
            if (widget.topBar != null) ...[
              widget.topBar!(context, vm.load),
              const SizedBox(height: 12),
            ],
            if (widget.hint != null) ...[
              Text(
                widget.hint!,
                style: const TextStyle(color: MadrasaTheme.muted, fontSize: 14),
              ),
              const SizedBox(height: 12),
            ],
            if (widget.showStudentStats) ...[
              StudentStatCards(
                wavulana: wavulanaCount,
                wasichana: wasichanaCount,
                jumla: jumlaCount,
                selectedGender: _selectedGender,
                onSelectGender: (gender) {
                  setState(() => _selectedGender = gender);
                },
              ),
              const SizedBox(height: 16),
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
            if (filteredRows.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 40),
                child: Text(
                  MadrasaCopy.emptyList,
                  textAlign: TextAlign.center,
                  style: TextStyle(color: MadrasaTheme.muted),
                ),
              )
            else
              ...filteredRows.map((row) {
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
                final isFemale = row.badge == 'KE';
                final isMale = row.badge == 'ME';
                final isNight = row.badge == 'Usiku';
                final badgeBg = isFemale
                    ? const Color(0x1AC2185B)
                    : isMale
                        ? const Color(0x1A0288D1)
                        : isNight
                            ? const Color(0x1A0B6E8F)
                            : MadrasaTheme.successBg;
                final badgeBorder = isFemale
                    ? const Color(0x4DC2185B)
                    : isMale
                        ? const Color(0x4D0288D1)
                        : isNight
                            ? const Color(0x4D0B6E8F)
                            : MadrasaTheme.successBorder;
                final badgeText = isFemale
                    ? StudentStatCards.femaleColor
                    : isMale
                        ? StudentStatCards.maleColor
                        : isNight
                            ? MadrasaTheme.secondary
                            : MadrasaTheme.successText;

                final hasTap =
                    widget.onRowTap != null || row.detailPath != null;

                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: AccentCard(
                    accent: isFemale
                        ? StudentStatCards.femaleColor
                        : isMale
                            ? StudentStatCards.maleColor
                            : isNight
                                ? MadrasaTheme.secondary
                                : MadrasaTheme.primary,
                    onTap: !hasTap
                        ? null
                        : () {
                            if (widget.onRowTap != null) {
                              widget.onRowTap!(context, row, vm.load);
                            } else if (row.detailPath != null) {
                              context.push(row.detailPath!);
                            }
                          },
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
                                    color: badgeBg,
                                    borderRadius: BorderRadius.circular(999),
                                    border: Border.all(color: badgeBorder),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      if (isNight) ...[
                                        Icon(
                                          Icons.nightlight_round,
                                          size: 12,
                                          color: badgeText,
                                        ),
                                        const SizedBox(width: 4),
                                      ],
                                      Text(
                                        row.badge!,
                                        style: TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.w700,
                                          color: badgeText,
                                        ),
                                      ),
                                    ],
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
                        if (hasTap)
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
