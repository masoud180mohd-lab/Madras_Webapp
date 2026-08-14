import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../data/models/models.dart';
import '../../../data/services/api_client.dart';
import '../../core/copy.dart';
import '../../core/theme.dart';
import '../../core/widgets/authenticated_photo.dart';
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
                  padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
                  itemCount: vm.rows.length,
                  itemBuilder: (context, index) {
                    final row = vm.rows[index];
                    return _RollTile(
                      api: api,
                      row: row,
                      editable: vm.canEdit,
                      onChanged: (yupo) =>
                          vm.setYupo(row.mwanafunzi.id, yupo),
                      onReason: (value) =>
                          vm.setSababu(row.mwanafunzi.id, value),
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
    Color color;
    if (!vm.canTakeAttendance) {
      text = MadrasaCopy.viewOnly;
      color = MadrasaTheme.muted;
    } else if (vm.alreadyRecorded) {
      text = vm.notice ?? MadrasaCopy.already;
      color = MadrasaTheme.primary;
    } else {
      text =
          '${MadrasaCopy.rollCall} · ${vm.presentCount}/${vm.rows.length} ${MadrasaCopy.present}';
      color = MadrasaTheme.forest;
    }
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(12, 12, 12, 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: const Border(
          left: BorderSide(color: MadrasaTheme.gold, width: 4),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            text,
            style: TextStyle(color: color, fontWeight: FontWeight.w600),
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
      decoration: const InputDecoration(labelText: MadrasaCopy.reason),
      onChanged: widget.onChanged,
    );
  }
}
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
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(8, 8, 8, 12),
        child: Column(
          children: [
            ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 8),
              leading: AuthenticatedPhoto(
                api: api,
                url: student.pichaUrl,
                fallbackLabel: student.jinaKamili,
              ),
              title: Text(
                student.jinaKamili,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              subtitle: Text(student.nambaYaUsajili),
              trailing: Switch.adaptive(
                value: row.yupo,
                onChanged: editable ? onChanged : null,
              ),
            ),
            Align(
              alignment: Alignment.centerLeft,
              child: Padding(
                padding: const EdgeInsets.only(left: 16),
                child: Text(
                  row.yupo ? MadrasaCopy.present : MadrasaCopy.absent,
                  style: TextStyle(
                    color: row.yupo ? MadrasaTheme.primary : MadrasaTheme.danger,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
            if (!row.yupo)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                child: _ReasonField(
                  key: ValueKey('reason-${student.id}'),
                  initial: row.sababu,
                  enabled: editable,
                  onChanged: onReason,
                ),
              ),
          ],
        ),
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
      decoration: const InputDecoration(labelText: MadrasaCopy.reason),
      onChanged: widget.onChanged,
    );
  }
}
