import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../core/copy.dart';
import '../../../core/pdf_downloader.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/hub_card.dart';
import '../../../core/widgets/student_stat_cards.dart';

class ClassHubView extends StatefulWidget {
  const ClassHubView({
    super.key,
    required this.darasa,
    required this.canTakeAttendance,
    required this.canViewStudents,
    this.canViewExams = false,
    this.canRecordExams = false,
    this.canRecordSabaq = false,
    this.canManageClasses = false,
    this.catalog,
    this.onClassUpdated,
  });

  final Darasa darasa;
  final bool canTakeAttendance;
  final bool canViewStudents;
  final bool canViewExams;
  final bool canRecordExams;
  final bool canRecordSabaq;
  final bool canManageClasses;
  final CatalogRepository? catalog;
  final VoidCallback? onClassUpdated;

  @override
  State<ClassHubView> createState() => _ClassHubViewState();
}

class _ClassHubViewState extends State<ClassHubView> {
  int? _wavulana;
  int? _wasichana;
  int? _jumla;
  late String _jina;
  String? _maelezo;

  @override
  void initState() {
    super.initState();
    _jina = widget.darasa.jina;
    _maelezo = widget.darasa.maelezo;
    _wavulana = widget.darasa.wavulana;
    _wasichana = widget.darasa.wasichana;
    _jumla = widget.darasa.idadiWanafunzi;
    _loadCountsIfNeeded();
  }

  @override
  void didUpdateWidget(covariant ClassHubView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.darasa.id != widget.darasa.id) {
      _jina = widget.darasa.jina;
      _maelezo = widget.darasa.maelezo;
      _wavulana = widget.darasa.wavulana;
      _wasichana = widget.darasa.wasichana;
      _jumla = widget.darasa.idadiWanafunzi;
      _loadCountsIfNeeded();
    }
  }

  Future<void> _loadCountsIfNeeded() async {
    final repo = widget.catalog;
    if (repo == null) {
      return;
    }
    try {
      final rows = await repo.wanafunzi(darasa: '${widget.darasa.id}');
      if (!mounted) {
        return;
      }
      final me = rows.where((r) => r.badge == 'ME').length;
      final ke = rows.where((r) => r.badge == 'KE').length;
      setState(() {
        _wavulana = me;
        _wasichana = ke;
        _jumla = rows.length;
      });
    } catch (_) {
      // Keep initial darasa counts if network fetch fails
    }
  }

  Future<void> _editClassDialog() async {
    final repo = widget.catalog;
    if (repo == null) return;
    final jinaCtrl = TextEditingController(text: _jina);
    final maelezoCtrl = TextEditingController(text: _maelezo ?? '');
    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Hariri darasa'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: jinaCtrl,
              decoration: const InputDecoration(labelText: 'Jina la darasa'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: maelezoCtrl,
              decoration: const InputDecoration(labelText: 'Maelezo (hiari)'),
              maxLines: 2,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Ghairi'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Hifadhi'),
          ),
        ],
      ),
    );
    if (saved != true || !mounted) return;
    final newJina = jinaCtrl.text.trim();
    if (newJina.isEmpty) return;
    try {
      await repo.haririDarasa(widget.darasa.id, {
        'jina': newJina,
        'maelezo': maelezoCtrl.text.trim(),
      });
      if (!mounted) return;
      setState(() {
        _jina = newJina;
        _maelezo = maelezoCtrl.text.trim();
      });
      widget.onClassUpdated?.call();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Darasa limesasishwa kikamilifu.')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  Future<void> _deleteClassDialog() async {
    final repo = widget.catalog;
    if (repo == null) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Futa darasa'),
        content: Text(
          'Una uhakika unataka kulifuta darasa la "$_jina"? Hatua hii haiwezekani kama lina wanafunzi au masomo.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Ghairi'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: MadrasaTheme.danger),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Futa'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await repo.futaDarasa(widget.darasa.id);
      if (!mounted) return;
      widget.onClassUpdated?.call();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Darasa limefutwa.')),
      );
      if (context.canPop()) {
        context.pop();
      } else {
        context.go('/madarasa');
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  Future<void> _openMsetoSheet() async {
    final repo = widget.catalog;
    if (repo == null) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => _DarasaMsetoSheet(
        darasaId: widget.darasa.id,
        darasaJina: _jina,
        canCreate: widget.canRecordExams || widget.canManageClasses,
        repository: repo,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final wavulana = _wavulana ?? 0;
    final wasichana = _wasichana ?? 0;
    final jumla = _jumla ?? (wavulana + wasichana);

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _jina,
                    style: const TextStyle(
                      fontFamily: MadrasaTheme.brandFont,
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                      color: MadrasaTheme.title,
                    ),
                  ),
                  if (_maelezo != null && _maelezo!.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      _maelezo!,
                      style: const TextStyle(color: MadrasaTheme.muted),
                    ),
                  ],
                ],
              ),
            ),
            if (widget.canManageClasses && widget.catalog != null) ...[
              IconButton(
                tooltip: 'Hariri darasa',
                icon: const Icon(
                  Icons.edit_outlined,
                  color: MadrasaTheme.primary,
                ),
                onPressed: _editClassDialog,
              ),
              IconButton(
                tooltip: 'Futa darasa',
                icon: const Icon(
                  Icons.delete_outline,
                  color: MadrasaTheme.danger,
                ),
                onPressed: _deleteClassDialog,
              ),
            ],
          ],
        ),
        const SizedBox(height: 16),
        StudentStatCards(
          wavulana: wavulana,
          wasichana: wasichana,
          jumla: jumla,
        ),
        const SizedBox(height: 20),
        if (widget.canTakeAttendance || widget.canViewStudents)
          HubCard(
            title: MadrasaCopy.rollCall,
            hint: widget.canTakeAttendance
                ? 'Rekodi yupo / hayupo'
                : MadrasaCopy.viewOnly,
            watermarkIcon: Icons.fact_check_rounded,
            onTap: () =>
                context.push('/madarasa/${widget.darasa.id}/mahudhurio'),
          ),
        if (widget.canViewStudents)
          HubCard(
            title: MadrasaCopy.classStudents,
            hint:
                '$jumla wanafunzi (Wanaume: $wavulana · Wanawake: $wasichana) · Sabaq na Ripoti',
            watermarkIcon: Icons.groups_rounded,
            onTap: () {
              final encoded = Uri.encodeComponent(_jina);
              context.push(
                '/madarasa/${widget.darasa.id}/wanafunzi?jina=$encoded',
              );
            },
          ),
        if ((widget.canViewExams || widget.canViewStudents) &&
            widget.catalog != null)
          HubCard(
            title: 'Mseto wa Mitihani na Matokeo ya Jumla',
            hint:
                'Unganisha mitihani ya muhula, tazama nafasi za wanafunzi na pakua PDF ya jumla',
            watermarkIcon: Icons.emoji_events_outlined,
            onTap: _openMsetoSheet,
          ),
      ],
    );
  }
}

class _DarasaMsetoSheet extends StatefulWidget {
  const _DarasaMsetoSheet({
    required this.darasaId,
    required this.darasaJina,
    required this.canCreate,
    required this.repository,
  });

  final int darasaId;
  final String darasaJina;
  final bool canCreate;
  final CatalogRepository repository;

  @override
  State<_DarasaMsetoSheet> createState() => _DarasaMsetoSheetState();
}

class _DarasaMsetoSheetState extends State<_DarasaMsetoSheet> {
  Future<Map<String, dynamic>>? _future;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    setState(() {
      _future = widget.repository.darasaMiseto(widget.darasaId);
    });
  }

  Future<void> _createMsetoDialog() async {
    final jinaCtrl = TextEditingController();
    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Unda Mseto wa Mitihani'),
        content: TextField(
          controller: jinaCtrl,
          decoration: const InputDecoration(
            labelText: 'Jina la mseto (mf. Mtihani wa Muhula wa 1)',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Ghairi'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Unda'),
          ),
        ],
      ),
    );
    if (saved != true || !mounted) return;
    final jina = jinaCtrl.text.trim();
    if (jina.isEmpty) return;
    try {
      await widget.repository.undaMseto(
        darasaId: widget.darasaId,
        jina: jina,
      );
      if (!mounted) return;
      _reload();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Mseto wa mitihani umeundwa.')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  Future<void> _openRipotiJumla(Map<String, dynamic> mseto) async {
    final msetoId = (mseto['id'] as num?)?.toInt() ?? 0;
    final jina = mseto['jina']?.toString() ?? 'Matokeo ya Jumla';
    if (msetoId <= 0) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => _MsetoRipotiSheet(
        darasaId: widget.darasaId,
        msetoId: msetoId,
        msetoJina: jina,
        darasaJina: widget.darasaJina,
        repository: widget.repository,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.75,
      minChildSize: 0.45,
      maxChildSize: 0.95,
      builder: (ctx, scrollController) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Mseto wa Mitihani',
                        style: TextStyle(
                          fontFamily: MadrasaTheme.brandFont,
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: MadrasaTheme.title,
                        ),
                      ),
                      Text(
                        widget.darasaJina,
                        style: const TextStyle(
                          color: MadrasaTheme.muted,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
                if (widget.canCreate)
                  FilledButton.icon(
                    onPressed: _createMsetoDialog,
                    icon: const Icon(Icons.add_rounded, size: 18),
                    label: const Text('Unda mseto'),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Expanded(
              child: FutureBuilder<Map<String, dynamic>>(
                future: _future,
                builder: (ctx, snap) {
                  if (snap.connectionState != ConnectionState.done) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  if (snap.hasError) {
                    return Center(
                      child: Text(MadrasaCopy.humanizeError(snap.error!)),
                    );
                  }
                  final raw = snap.data ?? const {};
                  final items = (raw['miseto'] as List? ?? const [])
                      .whereType<Map<String, dynamic>>()
                      .toList();
                  if (items.isEmpty) {
                    return const Center(
                      child: Text(
                        'Hakuna mseto wa mitihani ulioundwa kwa darasa hili bado.',
                        style: TextStyle(color: MadrasaTheme.muted),
                        textAlign: TextAlign.center,
                      ),
                    );
                  }
                  return ListView.separated(
                    controller: scrollController,
                    itemCount: items.length,
                    separatorBuilder: (c, idx) => const SizedBox(height: 8),
                    itemBuilder: (ctx, i) {
                      final m = items[i];
                      final jina = m['jina']?.toString() ?? '-';
                      final mwaka = m['mwaka']?.toString();
                      final muhula = m['muhula']?.toString();
                      final tarehe = m['tarehe']?.toString() ?? '';
                      final count = (m['idadi_mitihani'] as num?)?.toInt() ?? 0;
                      final metaParts = <String>[
                        'Mitihani: $count',
                        if (mwaka != null && mwaka.isNotEmpty) mwaka,
                        if (muhula != null && muhula.isNotEmpty) muhula,
                        if (tarehe.isNotEmpty) tarehe,
                      ];
                      return Card(
                        margin: EdgeInsets.zero,
                        child: ListTile(
                          leading: const CircleAvatar(
                            backgroundColor: MadrasaTheme.outlineSoft,
                            foregroundColor: MadrasaTheme.primary,
                            child: Icon(Icons.emoji_events_outlined),
                          ),
                          title: Text(
                            jina,
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          subtitle: Text(metaParts.join(' · ')),
                          trailing: const Icon(Icons.chevron_right_rounded),
                          onTap: () => _openRipotiJumla(m),
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MsetoRipotiSheet extends StatefulWidget {
  const _MsetoRipotiSheet({
    required this.darasaId,
    required this.msetoId,
    required this.msetoJina,
    required this.darasaJina,
    required this.repository,
  });

  final int darasaId;
  final int msetoId;
  final String msetoJina;
  final String darasaJina;
  final CatalogRepository repository;

  @override
  State<_MsetoRipotiSheet> createState() => _MsetoRipotiSheetState();
}

class _MsetoRipotiSheetState extends State<_MsetoRipotiSheet> {
  Future<Map<String, dynamic>>? _future;
  bool _downloading = false;

  @override
  void initState() {
    super.initState();
    _future = widget.repository.ripotiJumla(widget.darasaId, widget.msetoId);
  }

  Future<void> _downloadPdf() async {
    setState(() => _downloading = true);
    try {
      final bytes = await widget.repository.downloadMatokeoJumlaPdf(
        widget.darasaId,
        widget.msetoId,
      );
      if (!mounted) return;
      await PdfDownloader.saveAndOpen(
        context,
        bytes: bytes,
        filename: 'Matokeo_Jumla_${widget.darasaId}_${widget.msetoId}.pdf',
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.85,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      builder: (ctx, scrollController) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.msetoJina,
                        style: const TextStyle(
                          fontFamily: MadrasaTheme.brandFont,
                          fontSize: 19,
                          fontWeight: FontWeight.w700,
                          color: MadrasaTheme.title,
                        ),
                      ),
                      Text(
                        'Matokeo ya Jumla · ${widget.darasaJina}',
                        style: const TextStyle(
                          color: MadrasaTheme.muted,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
                OutlinedButton.icon(
                  onPressed: _downloading ? null : _downloadPdf,
                  icon: _downloading
                      ? const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.picture_as_pdf_outlined, size: 18),
                  label: const Text('PDF'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Expanded(
              child: FutureBuilder<Map<String, dynamic>>(
                future: _future,
                builder: (ctx, snap) {
                  if (snap.connectionState != ConnectionState.done) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  if (snap.hasError) {
                    return Center(
                      child: Text(MadrasaCopy.humanizeError(snap.error!)),
                    );
                  }
                  final data = snap.data ?? const {};
                  final mitihani = (data['mitihani'] as List? ?? const [])
                      .whereType<Map<String, dynamic>>()
                      .toList();
                  final ripoti = (data['ripoti'] as List? ?? const [])
                      .whereType<Map<String, dynamic>>()
                      .toList();
                  if (ripoti.isEmpty) {
                    return const Center(
                      child: Text(
                        'Hakuna matokeo kwenye mseto huu bado.',
                        style: TextStyle(color: MadrasaTheme.muted),
                      ),
                    );
                  }
                  return ListView.separated(
                    controller: scrollController,
                    itemCount: ripoti.length,
                    separatorBuilder: (c, idx) => const SizedBox(height: 8),
                    itemBuilder: (ctx, i) {
                      final r = ripoti[i];
                      final nafasi = r['nafasi']?.toString() ?? '-';
                      final jina = r['jina_kamili']?.toString() ?? '-';
                      final jumla = r['jumla']?.toString() ?? '0';
                      final wastani = r['wastani']?.toString() ?? '0';
                      final daraja = r['daraja']?.toString() ?? '-';
                      final hali = r['hali']?.toString() ?? '-';
                      final alama = (r['alama'] as List? ?? const []);

                      final subjectScores = <String>[];
                      for (var idx = 0;
                          idx < mitihani.length && idx < alama.length;
                          idx++) {
                        final sName = mitihani[idx]['somo']?.toString() ?? '';
                        final val = alama[idx];
                        subjectScores.add('$sName: ${val ?? "-"}');
                      }

                      return Card(
                        margin: EdgeInsets.zero,
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  CircleAvatar(
                                    radius: 16,
                                    backgroundColor: MadrasaTheme.primary,
                                    foregroundColor: Colors.white,
                                    child: Text(
                                      nafasi,
                                      style: const TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Text(
                                      jina,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        fontSize: 15,
                                      ),
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 4,
                                    ),
                                    decoration: BoxDecoration(
                                      color: MadrasaTheme.outlineSoft,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      'Daraja $daraja · $hali',
                                      style: const TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w600,
                                        color: MadrasaTheme.primary,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              Text(
                                'Jumla: $jumla · Wastani: $wastani%',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 13,
                                  color: MadrasaTheme.ink,
                                ),
                              ),
                              if (subjectScores.isNotEmpty) ...[
                                const SizedBox(height: 4),
                                Text(
                                  subjectScores.join('  |  '),
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
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
