import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../../data/services/api_exception.dart';
import '../../../core/copy.dart';
import '../../../core/pdf_downloader.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../../core/widgets/student_stat_cards.dart';
import '../../auth/view_models/auth_view_model.dart';

class HifdhuStudentsView extends StatefulWidget {
  const HifdhuStudentsView({
    super.key,
    this.somoId,
    this.darasaId,
    this.darasaJina,
    required this.repository,
  });

  final int? somoId;
  final int? darasaId;
  final String? darasaJina;
  final CatalogRepository repository;

  bool get isDarasaMode => darasaId != null;

  @override
  State<HifdhuStudentsView> createState() => _HifdhuStudentsViewState();
}

class _HifdhuStudentsViewState extends State<HifdhuStudentsView> {
  bool _loading = true;
  String? _error;
  SubjectDetail? _somo;
  List<Mwanafunzi> _students = const [];
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';
  String? _selectedGender;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      if (widget.isDarasaMode) {
        _students = await widget.repository.wanafunziDarasa(widget.darasaId!);
      } else {
        final results = await Future.wait([
          widget.repository.somoDetail(widget.somoId!),
          widget.repository.wanafunziHifdhu(widget.somoId!),
        ]);
        _somo = results[0] as SubjectDetail;
        _students = results[1] as List<Mwanafunzi>;
      }
    } on ApiException catch (error) {
      _error = error.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia orodha ya wanafunzi.';
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _openRipotiSheet(Mwanafunzi student) async {
    final aina = widget.isDarasaMode ? 'Darasa' : 'Usiku';
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => _StudentRipotiSheet(
        student: student,
        aina: aina,
        repository: widget.repository,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(_error!, textAlign: TextAlign.center),
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

    AuthViewModel? auth;
    try {
      auth = context.watch<AuthViewModel>();
    } catch (_) {
      auth = null;
    }
    final canSabaq = auth?.profile?.canRecordSabaq ?? true;
    final aina = widget.isDarasaMode ? 'Darasa' : 'Usiku';
    final title = widget.isDarasaMode
        ? 'Wanafunzi: ${widget.darasaJina ?? "Darasa"}'
        : 'Wanafunzi: ${_somo?.jina ?? "Hifdhu"}';

    final wavulanaCount = _students.where((s) => s.jinsia == 'ME').length;
    final wasichanaCount = _students.where((s) => s.jinsia == 'KE').length;

    final query = _searchQuery;
    final filtered = _students.where((s) {
      if (_selectedGender != null && s.jinsia != _selectedGender) {
        return false;
      }
      if (query.isEmpty) return true;
      return s.jinaKamili.toLowerCase().contains(query) ||
          s.nambaYaUsajili.toLowerCase().contains(query);
    }).toList();

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        Text(
          title,
          style: const TextStyle(
            fontFamily: MadrasaTheme.brandFont,
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: MadrasaTheme.title,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Jumla ya wanafunzi: ${_students.length}',
          style: const TextStyle(color: MadrasaTheme.muted, fontSize: 13),
        ),
        const SizedBox(height: 14),
        StudentStatCards(
          wavulana: wavulanaCount,
          wasichana: wasichanaCount,
          jumla: _students.length,
          selectedGender: _selectedGender,
          onSelectGender: (g) => setState(() => _selectedGender = g),
        ),
        const SizedBox(height: 14),
        TextField(
          controller: _searchController,
          decoration: InputDecoration(
            hintText: 'Tafuta mwanafunzi...',
            prefixIcon: const Icon(Icons.search),
            suffixIcon: _searchQuery.isNotEmpty
                ? IconButton(
                    icon: const Icon(Icons.clear, size: 18),
                    onPressed: () {
                      _searchController.clear();
                      setState(() => _searchQuery = '');
                    },
                  )
                : null,
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 14,
              vertical: 10,
            ),
          ),
          onChanged: (val) {
            setState(() => _searchQuery = val.trim().toLowerCase());
          },
        ),
        const SizedBox(height: 16),
        if (filtered.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 40),
            child: Text(
              _searchQuery.isNotEmpty
                  ? 'Hakuna mwanafunzi aliyepatikana.'
                  : 'Hakuna mwanafunzi aliyesajiliwa.',
              textAlign: TextAlign.center,
              style: const TextStyle(color: MadrasaTheme.muted),
            ),
          )
        else
          ...filtered.map((s) {
            final isFemale = s.jinsia == 'KE';
            return Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: AccentCard(
                accent: isFemale
                    ? StudentStatCards.femaleColor
                    : StudentStatCards.maleColor,
                onTap: () => context.push('/wanafunzi/${s.id}'),
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 20,
                      backgroundColor: isFemale
                          ? const Color(0x1AC2185B)
                          : const Color(0x1A0288D1),
                      child: Text(
                        s.jinaKamili.isNotEmpty
                            ? s.jinaKamili[0].toUpperCase()
                            : '?',
                        style: TextStyle(
                          color: isFemale
                              ? StudentStatCards.femaleColor
                              : StudentStatCards.maleColor,
                          fontWeight: FontWeight.w800,
                          fontSize: 16,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            s.jinaKamili,
                            style: const TextStyle(
                              fontWeight: FontWeight.w700,
                              fontSize: 15,
                              color: MadrasaTheme.title,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '${s.nambaYaUsajili} · ${isFemale ? "KE" : "ME"}',
                            style: const TextStyle(
                              fontSize: 12,
                              color: MadrasaTheme.muted,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (canSabaq) ...[
                          FilledButton(
                            onPressed: () => context.push(
                              '/wanafunzi/${s.id}/sabaq?aina=$aina${widget.somoId != null ? "&somoId=${widget.somoId}" : ""}',
                              extra: s,
                            ),
                            style: FilledButton.styleFrom(
                              backgroundColor: MadrasaTheme.primary,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 6,
                              ),
                              visualDensity: VisualDensity.compact,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(6),
                              ),
                            ),
                            child: const Text(
                              'Sabaq',
                              style: TextStyle(
                                fontWeight: FontWeight.w700,
                                fontSize: 13,
                              ),
                            ),
                          ),
                          const SizedBox(width: 6),
                        ],
                        OutlinedButton(
                          onPressed: () => _openRipotiSheet(s),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: MadrasaTheme.secondary,
                            side: const BorderSide(
                              color: MadrasaTheme.secondary,
                            ),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 6,
                            ),
                            visualDensity: VisualDensity.compact,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(6),
                            ),
                          ),
                          child: const Text(
                            'Ripoti',
                            style: TextStyle(
                              fontWeight: FontWeight.w700,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          }),
      ],
    );
  }
}

class _StudentRipotiSheet extends StatefulWidget {
  const _StudentRipotiSheet({
    required this.student,
    required this.aina,
    required this.repository,
  });

  final Mwanafunzi student;
  final String aina;
  final CatalogRepository repository;

  @override
  State<_StudentRipotiSheet> createState() => _StudentRipotiSheetState();
}

class _StudentRipotiSheetState extends State<_StudentRipotiSheet> {
  String _muda = 'wote';
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _data;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      _data = await widget.repository.ripotiMwanafunzi(
        widget.student.id,
        aina: widget.aina,
        muda: _muda,
      );
    } on ApiException catch (e) {
      _error = e.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia ripoti.';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final mahudhurio =
        (_data?['mahudhurio'] as List<dynamic>? ?? const [])
            .whereType<Map<String, dynamic>>()
            .toList();
    final sabaq =
        (_data?['sabaq'] as List<dynamic>? ?? const [])
            .whereType<Map<String, dynamic>>()
            .toList();

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.85,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      builder: (context, scrollController) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Ripoti: ${widget.student.jinaKamili}',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: MadrasaTheme.title,
                          ),
                        ),
                        Text(
                          'Kipindi cha ${widget.aina} · ${widget.student.nambaYaUsajili}',
                          style: const TextStyle(
                            color: MadrasaTheme.muted,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      Navigator.pop(context);
                      context.push('/wanafunzi/${widget.student.id}?tab=rekodi');
                    },
                    child: const Text('Wasifu Kamili'),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    for (final entry in const [
                      ('wote', 'Muda Wote'),
                      ('wiki', 'Wiki Hii'),
                      ('mwezi_huu', 'Mwezi Huu'),
                      ('mwezi_uliopita', 'Mwezi Uliopita'),
                    ])
                      Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(entry.$2),
                          selected: _muda == entry.$1,
                          onSelected: (v) {
                            if (v) {
                              setState(() => _muda = entry.$1);
                              _load();
                            }
                          },
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: () async {
                      try {
                        final bytes =
                            await widget.repository.downloadMahudhurioPdf(
                          widget.student.id,
                          aina: widget.aina,
                          muda: _muda,
                        );
                        if (!context.mounted) return;
                        await PdfDownloader.saveAndOpen(
                          context,
                          bytes: bytes,
                          filename:
                              'Mahudhurio_${widget.aina}_${widget.student.id}_$_muda.pdf',
                        );
                      } catch (e) {
                        if (!context.mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
                        );
                      }
                    },
                    icon: const Icon(Icons.picture_as_pdf_outlined, size: 16),
                    label: const Text('PDF ya Mahudhurio'),
                  ),
                  OutlinedButton.icon(
                    onPressed: () async {
                      try {
                        final bytes = await widget.repository.downloadSabaqPdf(
                          widget.student.id,
                          aina: widget.aina,
                          muda: _muda,
                        );
                        if (!context.mounted) return;
                        await PdfDownloader.saveAndOpen(
                          context,
                          bytes: bytes,
                          filename:
                              'Sabaq_${widget.aina}_${widget.student.id}_$_muda.pdf',
                        );
                      } catch (e) {
                        if (!context.mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
                        );
                      }
                    },
                    icon: const Icon(Icons.picture_as_pdf_outlined, size: 16),
                    label: const Text('PDF ya Sabaq'),
                  ),
                ],
              ),
              const Divider(height: 20),
              Expanded(
                child: _loading
                    ? const Center(child: CircularProgressIndicator())
                    : _error != null
                    ? Center(child: Text(_error!))
                    : ListView(
                        controller: scrollController,
                        children: [
                          Text(
                            'Rekodi za Sabaq (${sabaq.length})',
                            style: const TextStyle(
                              fontWeight: FontWeight.w800,
                              color: MadrasaTheme.primary,
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(height: 8),
                          if (sabaq.isEmpty)
                            const Text(
                              'Hakuna rekodi za sabaq katika muda huu.',
                              style: TextStyle(color: MadrasaTheme.muted),
                            )
                          else
                            ...sabaq.map((r) {
                              final mapande =
                                  (r['mapande'] as List<dynamic>? ?? const [])
                                      .whereType<Map<String, dynamic>>()
                                      .toList();
                              return Card(
                                margin: const EdgeInsets.only(bottom: 8),
                                child: Padding(
                                  padding: const EdgeInsets.all(12),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          Expanded(
                                            child: Text(
                                              '${r['tarehe']} · ${r['sura'] ?? '-'}'
                                              '${r['aya_kuanzia'] != null ? " (${r['aya_kuanzia']}-${r['aya_kuishia']})" : ""}',
                                              style: const TextStyle(
                                                fontWeight: FontWeight.w700,
                                              ),
                                            ),
                                          ),
                                          Text(
                                            '${r['hali'] ?? ''}',
                                            style: const TextStyle(
                                              fontWeight: FontWeight.w700,
                                              color: MadrasaTheme.primary,
                                            ),
                                          ),
                                        ],
                                      ),
                                      if (mapande.isNotEmpty) ...[
                                        const SizedBox(height: 4),
                                        Text(
                                          'Mapande: ${mapande.map((p) => "${p['sura']} (${p['aya_kuanzia'] ?? ''}-${p['aya_kuishia'] ?? ''}) [${p['hali']}]").join(", ")}',
                                          style: const TextStyle(
                                            fontSize: 12,
                                            color: MadrasaTheme.secondary,
                                          ),
                                        ),
                                      ],
                                      if ((r['maoni'] as String?)?.isNotEmpty ==
                                          true) ...[
                                        const SizedBox(height: 4),
                                        Text(
                                          'Maoni: ${r['maoni']}',
                                          style: const TextStyle(
                                            fontSize: 12,
                                            color: MadrasaTheme.muted,
                                          ),
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                              );
                            }),
                          const SizedBox(height: 16),
                          Text(
                            'Mahudhurio (${mahudhurio.length})',
                            style: const TextStyle(
                              fontWeight: FontWeight.w800,
                              color: MadrasaTheme.primary,
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(height: 8),
                          if (mahudhurio.isEmpty)
                            const Text(
                              'Hakuna rekodi za mahudhurio katika muda huu.',
                              style: TextStyle(color: MadrasaTheme.muted),
                            )
                          else
                            ...mahudhurio.map((m) {
                              final yupo = m['yupo'] == true;
                              return ListTile(
                                dense: true,
                                contentPadding: EdgeInsets.zero,
                                title: Text('${m['tarehe']}'),
                                subtitle:
                                    (m['sababu_kama_hayupo'] as String?)
                                            ?.isNotEmpty ==
                                        true
                                    ? Text('Sababu: ${m['sababu_kama_hayupo']}')
                                    : null,
                                trailing: Text(
                                  yupo ? 'Yupo' : 'Hayupo',
                                  style: TextStyle(
                                    fontWeight: FontWeight.w700,
                                    color: yupo
                                        ? MadrasaTheme.successText
                                        : MadrasaTheme.dangerText,
                                  ),
                                ),
                              );
                            }),
                        ],
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
