import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../data/models/models.dart';
import '../../../../data/services/api_client.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../../core/widgets/authenticated_photo.dart';
import '../view_models/roll_call_view_model.dart';

class RollCallView extends StatefulWidget {
  const RollCallView({super.key, required this.viewModel});

  final RollCallViewModel viewModel;

  @override
  State<RollCallView> createState() => _RollCallViewState();
}

class _RollCallViewState extends State<RollCallView> {
  @override
  void initState() {
    super.initState();
    widget.viewModel.load();
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<ApiClient>();
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.viewModel.darasa.jina),
      ),
      body: ListenableBuilder(
        listenable: widget.viewModel,
        builder: (context, _) {
          final vm = widget.viewModel;
          if (vm.loading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (vm.error != null && vm.rows.isEmpty) {
            return Center(child: Text(vm.error!));
          }
          if (vm.rows.isEmpty) {
            return const Center(child: Text(MadrasaCopy.emptyRoster));
          }
          return Column(
            children: [
              _Banner(viewModel: vm),
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  itemCount: vm.rows.length,
                  itemBuilder: (context, index) {
                    final row = vm.rows[index];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: _RollTile(
                        api: api,
                        row: row,
                        editable: vm.canEdit,
                        onChanged: (yupo) =>
                            vm.setYupo(row.mwanafunzi.id, yupo),
                        onReason: (value) =>
                            vm.setSababu(row.mwanafunzi.id, value),
                      ),
                    );
                  },
                ),
              ),
              if (vm.canEdit)
                SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                    child: FilledButton(
                      onPressed: vm.saving ? null : () => vm.save(),
                      child: vm.saving
                          ? const SizedBox(
                              height: 22,
                              width: 22,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Text(MadrasaCopy.save),
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

class _Banner extends StatelessWidget {
  const _Banner({required this.viewModel});

  final RollCallViewModel viewModel;

  @override
  Widget build(BuildContext context) {
    final vm = viewModel;
    String text;
    Color accent;
    if (!vm.canTakeAttendance) {
      text = MadrasaCopy.viewOnly;
      accent = MadrasaTheme.muted;
    } else if (vm.alreadyRecorded) {
      text = vm.notice ?? MadrasaCopy.already;
      accent = MadrasaTheme.primary;
    } else {
      text =
          '${MadrasaCopy.rollCall} · ${vm.presentCount}/${vm.rows.length} ${MadrasaCopy.present}';
      accent = MadrasaTheme.gold;
    }
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: AccentCard(
        accent: accent,
        accentWidth: 4,
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              text,
              style: TextStyle(
                color: accent == MadrasaTheme.gold ? MadrasaTheme.title : accent,
                fontWeight: FontWeight.w700,
              ),
            ),
            if (vm.error != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  vm.error!,
                  style: const TextStyle(color: MadrasaTheme.danger),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _RollTile extends StatelessWidget {
  const _RollTile({
    required this.api,
    required this.row,
    required this.editable,
    required this.onChanged,
    required this.onReason,
  });

  final ApiClient api;
  final RollDraft row;
  final bool editable;
  final ValueChanged<bool> onChanged;
  final ValueChanged<String> onReason;

  @override
  Widget build(BuildContext context) {
    final student = row.mwanafunzi;
    final accent = row.yupo ? MadrasaTheme.primary : MadrasaTheme.danger;
    return AccentCard(
      accent: accent,
      padding: const EdgeInsets.fromLTRB(14, 12, 12, 14),
      child: Column(
        children: [
          Row(
            children: [
              AuthenticatedPhoto(
                api: api,
                url: student.pichaUrl,
                fallbackLabel: student.jinaKamili,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      student.jinaKamili,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: MadrasaTheme.ink,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      student.nambaYaUsajili,
                      style: const TextStyle(
                        fontSize: 13,
                        color: MadrasaTheme.muted,
                      ),
                    ),
                    const SizedBox(height: 8),
                    _StatusBadge(yupo: row.yupo),
                  ],
                ),
              ),
              Switch.adaptive(
                value: row.yupo,
                activeThumbColor: MadrasaTheme.primary,
                onChanged: editable ? onChanged : null,
              ),
            ],
          ),
          if (!row.yupo)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: _ReasonField(
                key: ValueKey('reason-${student.id}'),
                initial: row.sababu,
                enabled: editable,
                onChanged: onReason,
              ),
            ),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.yupo});

  final bool yupo;

  @override
  Widget build(BuildContext context) {
    final bg = yupo ? MadrasaTheme.successBg : MadrasaTheme.dangerBg;
    final border = yupo ? MadrasaTheme.successBorder : MadrasaTheme.dangerBorder;
    final fg = yupo ? MadrasaTheme.successText : MadrasaTheme.dangerText;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            yupo ? Icons.check_circle : Icons.cancel,
            size: 15,
            color: fg,
          ),
          const SizedBox(width: 6),
          Text(
            yupo ? MadrasaCopy.present : MadrasaCopy.absent,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: fg,
            ),
          ),
        ],
      ),
    );
  }
}

class _ReasonField extends StatefulWidget {
  const _ReasonField({
    super.key,
    required this.initial,
    required this.enabled,
    required this.onChanged,
  });

  final String initial;
  final bool enabled;
  final ValueChanged<String> onChanged;

  @override
  State<_ReasonField> createState() => _ReasonFieldState();
}

class _ReasonFieldState extends State<_ReasonField> {
  late final TextEditingController _controller = TextEditingController(
    text: widget.initial,
  );

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _controller,
      enabled: widget.enabled,
      decoration: const InputDecoration(
        labelText: MadrasaCopy.reason,
        isDense: true,
      ),
      onChanged: widget.onChanged,
    );
  }
}
