import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../../data/services/api_exception.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';

class ExamResultsView extends StatefulWidget {
  const ExamResultsView({
    super.key,
    required this.mtihaniId,
    required this.repository,
    this.editable = false,
  });

  final int mtihaniId;
  final CatalogRepository repository;
  final bool editable;

  @override
  State<ExamResultsView> createState() => _ExamResultsViewState();
}

class _ExamResultsViewState extends State<ExamResultsView> {
  bool _loading = true;
  bool _saving = false;
  String? _error;
  ExamResults? _data;
  final Map<int, TextEditingController> _controllers = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await widget.repository.matokeo(widget.mtihaniId);
      for (final c in _controllers.values) {
        c.dispose();
      }
      _controllers.clear();
      for (final row in data.rekodi) {
        _controllers[row.mwanafunziId] = TextEditingController(
          text: row.maksi == null ? '' : row.maksi!.toStringAsFixed(0),
        );
      }
      _data = data;
    } on ApiException catch (error) {
      _error = error.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia matokeo.';
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _save() async {
    final data = _data;
    if (data == null) {
      return;
    }
    final rekodi = <Map<String, dynamic>>[];
    for (final row in data.rekodi) {
      final text = _controllers[row.mwanafunziId]?.text.trim() ?? '';
      if (text.isEmpty) {
        continue;
      }
      final maksi = double.tryParse(text);
      if (maksi == null || maksi < 0 || maksi > 100) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Maksi ya ${row.jinaKamili} si sahihi (0–100).'),
          ),
        );
        return;
      }
      rekodi.add({'mwanafunzi': row.mwanafunziId, 'maksi': maksi});
    }
    if (rekodi.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Weka angalau maksi moja.')),
      );
      return;
    }
    setState(() => _saving = true);
    try {
      await widget.repository.hifadhiMaksi(widget.mtihaniId, rekodi);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Maksi zimehifadhiwa.')),
        );
      }
      await _load();
    } on ApiException catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.message)),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Imeshindikana kuhifadhi maksi.')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null || _data == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(_error ?? MadrasaCopy.emptyList, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: _load,
                child: const Text(MadrasaCopy.retry),
              ),
            ],
          ),
        ),
      );
    }

    final data = _data!;
    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
            children: [
              AccentCard(
                accent: MadrasaTheme.gold,
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      data.jina,
                      style: const TextStyle(
                        fontFamily: MadrasaTheme.brandFont,
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: MadrasaTheme.title,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Tarehe: ${data.tarehe}',
                      style: const TextStyle(color: MadrasaTheme.muted),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              ...data.rekodi.asMap().entries.map((entry) {
                final index = entry.key;
                final row = entry.value;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: AccentCard(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 10,
                    ),
                    child: Row(
                      children: [
                        SizedBox(
                          width: 28,
                          child: Text(
                            '${index + 1}',
                            style: const TextStyle(
                              fontWeight: FontWeight.w800,
                              color: MadrasaTheme.gold,
                            ),
                          ),
                        ),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                row.jinaKamili,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              if (!widget.editable && row.daraja != null)
                                Text(
                                  '${row.daraja}${row.maelezo == null ? '' : ' · ${row.maelezo}'}',
                                  style: const TextStyle(
                                    color: MadrasaTheme.muted,
                                    fontSize: 13,
                                  ),
                                ),
                            ],
                          ),
                        ),
                        if (widget.editable)
                          SizedBox(
                            width: 72,
                            child: TextField(
                              controller: _controllers[row.mwanafunziId],
                              keyboardType: TextInputType.number,
                              inputFormatters: [
                                FilteringTextInputFormatter.allow(
                                  RegExp(r'[0-9.]'),
                                ),
                              ],
                              decoration: const InputDecoration(
                                isDense: true,
                                hintText: '0–100',
                              ),
                              textAlign: TextAlign.center,
                            ),
                          )
                        else
                          Text(
                            row.maksi == null
                                ? '—'
                                : row.maksi!.toStringAsFixed(0),
                            style: const TextStyle(
                              fontWeight: FontWeight.w800,
                              fontSize: 16,
                              color: MadrasaTheme.primary,
                            ),
                          ),
                      ],
                    ),
                  ),
                );
              }),
            ],
          ),
        ),
        if (widget.editable)
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _saving ? null : _save,
                  child: Text(
                    _saving ? 'Inahifadhi…' : MadrasaCopy.saveMarks,
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
