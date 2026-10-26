import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../../data/services/api_exception.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';

class _PandeDraft {
  final TextEditingController sura = TextEditingController();
  final TextEditingController ayaKuanzia = TextEditingController();
  final TextEditingController ayaKuishia = TextEditingController();
  String hali = 'Pasi';

  void dispose() {
    sura.dispose();
    ayaKuanzia.dispose();
    ayaKuishia.dispose();
  }
}

class RekodiSabaqView extends StatefulWidget {
  const RekodiSabaqView({
    super.key,
    required this.mwanafunziId,
    required this.repository,
    this.aina = 'Usiku',
    this.mwanafunzi,
    this.somoId,
  });

  final int mwanafunziId;
  final CatalogRepository repository;
  final String aina;
  final Mwanafunzi? mwanafunzi;
  final int? somoId;

  @override
  State<RekodiSabaqView> createState() => _RekodiSabaqViewState();
}

class _RekodiSabaqViewState extends State<RekodiSabaqView> {
  final _formKey = GlobalKey<FormState>();
  final _suraController = TextEditingController();
  final _ayaKuanziaController = TextEditingController();
  final _ayaKuishiaController = TextEditingController();
  final _maoniController = TextEditingController();
  final List<_PandeDraft> _mapande = [_PandeDraft()];

  String _hali = 'Kajua';
  bool _loading = false;
  bool _submitting = false;
  String? _error;
  Mwanafunzi? _mwanafunzi;

  @override
  void initState() {
    super.initState();
    _mwanafunzi = widget.mwanafunzi;
    if (_mwanafunzi == null) {
      _loadStudent();
    }
  }

  @override
  void dispose() {
    _suraController.dispose();
    _ayaKuanziaController.dispose();
    _ayaKuishiaController.dispose();
    _maoniController.dispose();
    for (final p in _mapande) {
      p.dispose();
    }
    super.dispose();
  }

  Future<void> _loadStudent() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final detail = await widget.repository.mwanafunziDetail(
        widget.mwanafunziId,
      );
      if (mounted) {
        setState(() {
          _mwanafunzi = Mwanafunzi(
            id: detail.id,
            jinaKamili: detail.jinaKamili,
            nambaYaUsajili: detail.nambaYaUsajili,
            jinsia: detail.jinsia,
            pichaUrl: detail.pichaUrl,
          );
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Imeshindikana kupakia taarifa za mwanafunzi.');
      }
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _save() async {
    if (_submitting) return;

    final sura = _suraController.text.trim();
    final ayaKuanzia = int.tryParse(_ayaKuanziaController.text.trim());
    final ayaKuishia = int.tryParse(_ayaKuishiaController.text.trim());
    final maoni = _maoniController.text.trim();

    final mapandePayload = <Map<String, dynamic>>[];
    if (widget.aina == 'Usiku') {
      for (final p in _mapande) {
        final ps = p.sura.text.trim();
        if (ps.isEmpty) continue;
        mapandePayload.add({
          'sura': ps,
          'aya_kuanzia': int.tryParse(p.ayaKuanzia.text.trim()),
          'aya_kuishia': int.tryParse(p.ayaKuishia.text.trim()),
          'hali': p.hali,
        });
      }
    }

    setState(() => _submitting = true);
    try {
      await widget.repository.rekodiSabaq(
        mwanafunziId: widget.mwanafunziId,
        aina: widget.aina,
        sura: sura.isEmpty ? null : sura,
        ayaKuanzia: ayaKuanzia,
        ayaKuishia: ayaKuishia,
        hali: _hali,
        maoni: maoni.isEmpty ? null : maoni,
        mapande: mapandePayload.isEmpty ? null : mapandePayload,
      );

      if (!mounted) return;

      final studentName = _mwanafunzi?.jinaKamili ?? 'Mwanafunzi';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Sabaq ya $studentName imehifadhiwa kikamilifu!'),
          backgroundColor: MadrasaTheme.primary,
        ),
      );
      context.pop(true);
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.message),
            backgroundColor: Colors.red.shade700,
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Imeshindikana kurekodi sabaq.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(_error!, textAlign: TextAlign.center),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: _loadStudent,
                  child: const Text(MadrasaCopy.retry),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final mwanafunzi = _mwanafunzi;
    final isFemale = mwanafunzi?.jinsia == 'KE';

    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.aina == 'Usiku' ? 'Rekodi Sabaq & Murajaa' : 'Rekodi Sabaq',
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (mwanafunzi != null) ...[
                AccentCard(
                  accent: isFemale
                      ? const Color(0xFFC2185B)
                      : const Color(0xFF0288D1),
                  padding: const EdgeInsets.all(14),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 24,
                        backgroundColor: isFemale
                            ? const Color(0x1AC2185B)
                            : const Color(0x1A0288D1),
                        child: Text(
                          mwanafunzi.jinaKamili.isNotEmpty
                              ? mwanafunzi.jinaKamili[0].toUpperCase()
                              : '?',
                          style: TextStyle(
                            color: isFemale
                                ? const Color(0xFFC2185B)
                                : const Color(0xFF0288D1),
                            fontWeight: FontWeight.w800,
                            fontSize: 18,
                          ),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              mwanafunzi.jinaKamili,
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.w700,
                                color: MadrasaTheme.title,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '${mwanafunzi.nambaYaUsajili} · Kipindi cha ${widget.aina}',
                              style: const TextStyle(
                                fontSize: 13,
                                color: MadrasaTheme.muted,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              AccentCard(
                accent: MadrasaTheme.primary,
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.menu_book_rounded,
                          color: MadrasaTheme.primary,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          widget.aina == 'Usiku'
                              ? 'Sura ya Kuhifadhi (Sabaq Mpya)'
                              : 'Sabaq ya Leo',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                            color: MadrasaTheme.title,
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 20),
                    TextFormField(
                      controller: _suraController,
                      decoration: const InputDecoration(
                        labelText: 'Jina la Sura au Juzuu',
                        hintText: 'Mfano: Al-Baqarah au Juzuu 1',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.bookmark_border),
                      ),
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: _ayaKuanziaController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              labelText: 'Aya Kuanzia',
                              hintText: 'Mf. 1',
                              border: OutlineInputBorder(),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextFormField(
                            controller: _ayaKuishiaController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              labelText: 'Aya Kuishia',
                              hintText: 'Mf. 10',
                              border: OutlineInputBorder(),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Tathmini ya Mwalimu:',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: MadrasaTheme.title,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      children: [
                        _buildChoiceChip(
                          'Kajua',
                          'Ameijua',
                          MadrasaTheme.successBg,
                          MadrasaTheme.successText,
                        ),
                        _buildChoiceChip(
                          'Hajajua',
                          'Hajaijua',
                          MadrasaTheme.dangerBg,
                          MadrasaTheme.dangerText,
                        ),
                        _buildChoiceChip(
                          'Hajasikilizwa',
                          'Hajasikilizwa',
                          MadrasaTheme.surfaceMuted,
                          MadrasaTheme.ink,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              if (widget.aina == 'Usiku') ...[
                AccentCard(
                  accent: MadrasaTheme.secondary,
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(
                            Icons.autorenew_rounded,
                            color: MadrasaTheme.secondary,
                          ),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Mapande (Murajaa)',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                                color: MadrasaTheme.title,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'Unaweza kuongeza pande zaidi ya moja kulingana na alivyosoma mwanafunzi.',
                        style: TextStyle(
                          fontSize: 12,
                          color: MadrasaTheme.muted,
                        ),
                      ),
                      const Divider(height: 20),
                      for (var i = 0; i < _mapande.length; i++) ...[
                        _buildPandeRow(i),
                        const SizedBox(height: 12),
                      ],
                      OutlinedButton.icon(
                        onPressed: () {
                          setState(() => _mapande.add(_PandeDraft()));
                        },
                        icon: const Icon(Icons.add, size: 18),
                        label: const Text('Ongeza Pande Jingine'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              AccentCard(
                accent: MadrasaTheme.gold,
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.edit_note_rounded, color: MadrasaTheme.gold),
                        SizedBox(width: 8),
                        Text(
                          'Maoni ya Mwalimu',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                            color: MadrasaTheme.title,
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 20),
                    TextFormField(
                      controller: _maoniController,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        labelText: 'Maoni / Maelezo ya Murajaa (hiari)',
                        hintText:
                            'Mf. Amekariri vizuri juzuu ya 30, aendelee kufanya marudio...',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              FilledButton.icon(
                onPressed: _submitting ? null : _save,
                icon: _submitting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.check_circle_outline),
                label: Text(
                  _submitting ? 'Inahifadhi...' : 'Hifadhi Sabaq',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                style: FilledButton.styleFrom(
                  backgroundColor: MadrasaTheme.primary,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPandeRow(int index) {
    final draft = _mapande[index];
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: MadrasaTheme.surfaceMuted,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: MadrasaTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                'Pande #${index + 1}',
                style: const TextStyle(
                  fontWeight: FontWeight.w700,
                  color: MadrasaTheme.secondary,
                ),
              ),
              const Spacer(),
              if (_mapande.length > 1)
                IconButton(
                  icon: const Icon(
                    Icons.delete_outline,
                    color: MadrasaTheme.danger,
                    size: 20,
                  ),
                  visualDensity: VisualDensity.compact,
                  tooltip: 'Ondoa pande hili',
                  onPressed: () {
                    setState(() {
                      final removed = _mapande.removeAt(index);
                      removed.dispose();
                    });
                  },
                ),
            ],
          ),
          const SizedBox(height: 8),
          TextField(
            controller: draft.sura,
            decoration: const InputDecoration(
              labelText: 'Sura ya Pande',
              hintText: 'Mfano: Yasin',
              border: OutlineInputBorder(),
              isDense: true,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: draft.ayaKuanzia,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Kuanzia Aya',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: draft.ayaKuishia,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Kuishia Aya',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            children: [
              for (final entry in const [
                ('Pasi', 'Amepasi'),
                ('Makosa', 'Ana Makosa'),
                ('Feli', 'Amefeli'),
              ])
                ChoiceChip(
                  label: Text(entry.$2),
                  selected: draft.hali == entry.$1,
                  onSelected: (val) {
                    if (val) {
                      setState(() => draft.hali = entry.$1);
                    }
                  },
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildChoiceChip(
    String value,
    String label,
    Color bg,
    Color textColor,
  ) {
    final selected = _hali == value;
    return ChoiceChip(
      label: Text(
        label,
        style: TextStyle(
          fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
          color: selected ? textColor : MadrasaTheme.ink,
        ),
      ),
      selected: selected,
      selectedColor: bg,
      side: BorderSide(
        color: selected ? textColor : MadrasaTheme.border,
        width: selected ? 1.5 : 1,
      ),
      onSelected: (val) {
        if (val) {
          setState(() => _hali = value);
        }
      },
    );
  }
}
