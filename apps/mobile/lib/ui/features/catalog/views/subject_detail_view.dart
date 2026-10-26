import 'dart:io';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../../data/services/api_client.dart';
import '../../../../data/services/api_exception.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../../core/widgets/hub_card.dart';
import '../../../core/widgets/student_stat_cards.dart';
import '../../auth/view_models/auth_view_model.dart';

class SubjectDetailView extends StatefulWidget {
  const SubjectDetailView({
    super.key,
    required this.somoId,
    required this.repository,
  });

  final int somoId;
  final CatalogRepository repository;

  @override
  State<SubjectDetailView> createState() => _SubjectDetailViewState();
}

class _SubjectDetailViewState extends State<SubjectDetailView> {
  bool _loading = true;
  bool _busy = false;
  String? _error;
  SubjectDetail? _data;
  int? _openingId;
  List<Mwanafunzi> _hifdhuStudents = const [];

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
      final detail = await widget.repository.somoDetail(widget.somoId);
      _data = detail;
      if (detail.niLaHifdhu) {
        try {
          _hifdhuStudents = await widget.repository.wanafunziHifdhu(
            widget.somoId,
          );
        } catch (_) {
          _hifdhuStudents = const [];
        }
      }
    } on ApiException catch (error) {
      _error = error.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia taarifa za somo.';
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  bool _isImage(String name) {
    final lower = name.toLowerCase();
    return lower.endsWith('.png') ||
        lower.endsWith('.jpg') ||
        lower.endsWith('.jpeg') ||
        lower.endsWith('.webp') ||
        lower.endsWith('.gif');
  }

  Future<void> _openMaterial(SubjectMaterial item) async {
    final url = item.failiUrl;
    if (url == null || url.isEmpty) {
      return;
    }
    setState(() => _openingId = item.id);
    try {
      final api = context.read<ApiClient>();
      final response = await api.getBytes(url);
      final bytes = response.bodyBytes;
      if (_isImage(item.jinaLaFaili) && mounted) {
        await showDialog<void>(
          context: context,
          builder: (context) => Dialog(
            child: InteractiveViewer(
              child: Image.memory(Uint8List.fromList(bytes)),
            ),
          ),
        );
        return;
      }
      final dir = await getApplicationDocumentsDirectory();
      final safeName = item.jinaLaFaili.replaceAll(RegExp(r'[^\w.\-]+'), '_');
      final file = File('${dir.path}/nyenzo_${item.id}_$safeName');
      await file.writeAsBytes(bytes, flush: true);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Faili imehifadhiwa: ${file.path}'),
            duration: const Duration(seconds: 5),
          ),
        );
      }
    } on ApiException catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.message)),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Imeshindikana kufungua faili.')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _openingId = null);
      }
    }
  }

  Future<void> _uploadMaterial() async {
    final nameController = TextEditingController();
    PlatformFile? picked;
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setLocal) {
            return AlertDialog(
              title: const Text(MadrasaCopy.uploadMaterial),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: nameController,
                    decoration: const InputDecoration(
                      labelText: MadrasaCopy.materialName,
                    ),
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: () async {
                      final result = await FilePicker.platform.pickFiles(
                        withData: true,
                        type: FileType.custom,
                        allowedExtensions: const [
                          'pdf',
                          'doc',
                          'docx',
                          'ppt',
                          'pptx',
                          'xls',
                          'xlsx',
                          'txt',
                          'jpg',
                          'jpeg',
                          'png',
                          'webp',
                        ],
                      );
                      if (result == null || result.files.isEmpty) {
                        return;
                      }
                      setLocal(() {
                        picked = result.files.first;
                        if (nameController.text.trim().isEmpty) {
                          nameController.text = picked!.name;
                        }
                      });
                    },
                    icon: const Icon(Icons.attach_file),
                    label: Text(
                      picked?.name ?? MadrasaCopy.pickFile,
                    ),
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  child: const Text('Ghairi'),
                ),
                FilledButton(
                  onPressed: () => Navigator.pop(context, true),
                  child: const Text('Hifadhi'),
                ),
              ],
            );
          },
        );
      },
    );
    final file = picked;
    final jina = nameController.text.trim();
    nameController.dispose();
    if (!mounted) return;
    if (ok != true || file == null || file.bytes == null) {
      return;
    }
    if (jina.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Weka jina la faili.')),
      );
      return;
    }
    setState(() => _busy = true);
    try {
      await widget.repository.pakiaNyenzo(
        somoId: widget.somoId,
        jinaLaFaili: jina,
        bytes: file.bytes!,
        filename: file.name,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Nyenzo imepakia kikamilifu.')),
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
          const SnackBar(content: Text('Imeshindikana kupakia nyenzo.')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  Future<void> _createExam() async {
    final nameController = TextEditingController();
    var tarehe = DateTime.now();
    int? selectedMsetoId;
    final miseto = _data?.miseto ?? const [];

    final ok = await showDialog<bool>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setLocal) {
            return AlertDialog(
              title: const Text(MadrasaCopy.newExam),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      controller: nameController,
                      decoration: const InputDecoration(
                        labelText: MadrasaCopy.examName,
                      ),
                    ),
                    const SizedBox(height: 12),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text(MadrasaCopy.examDate),
                      subtitle: Text(DateFormat('yyyy-MM-dd').format(tarehe)),
                      trailing: const Icon(Icons.calendar_today),
                      onTap: () async {
                        final picked = await showDatePicker(
                          context: context,
                          initialDate: tarehe,
                          firstDate: DateTime(2020),
                          lastDate: DateTime(2100),
                        );
                        if (picked != null) {
                          setLocal(() => tarehe = picked);
                        }
                      },
                    ),
                    if (miseto.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      DropdownButtonFormField<int?>(
                        initialValue: selectedMsetoId,
                        isExpanded: true,
                        decoration: const InputDecoration(
                          labelText: 'Mseto wa Mitihani (hiari)',
                        ),
                        items: [
                          const DropdownMenuItem<int?>(
                            value: null,
                            child: Text('Bila mseto'),
                          ),
                          for (final m in miseto)
                            DropdownMenuItem<int?>(
                              value: m['id'] as int?,
                              child: Text('${m['jina'] ?? ''}'),
                            ),
                        ],
                        onChanged: (val) =>
                            setLocal(() => selectedMsetoId = val),
                      ),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  child: const Text('Ghairi'),
                ),
                FilledButton(
                  onPressed: () => Navigator.pop(context, true),
                  child: const Text('Hifadhi'),
                ),
              ],
            );
          },
        );
      },
    );
    final jina = nameController.text.trim();
    nameController.dispose();
    if (!mounted) return;
    if (ok != true) {
      return;
    }
    if (jina.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Weka jina la mtihani.')),
      );
      return;
    }
    setState(() => _busy = true);
    try {
      await widget.repository.undaMtihani(
        somoId: widget.somoId,
        jina: jina,
        tarehe: DateFormat('yyyy-MM-dd').format(tarehe),
        msetoId: selectedMsetoId,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Mtihani umesajiliwa.')),
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
          const SnackBar(content: Text('Imeshindikana kuongeza mtihani.')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  Future<void> _openMaendeleoSheet({required bool canSabaq}) async {
    final data = _data;
    if (data == null) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => _MaendeleoMchanaSheet(
        somo: data,
        repository: widget.repository,
        canSabaq: canSabaq,
      ),
    );
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
              Text(
                _error ?? MadrasaCopy.emptyList,
                textAlign: TextAlign.center,
              ),
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
    AuthViewModel? auth;
    try {
      auth = context.watch<AuthViewModel>();
    } catch (_) {
      auth = null;
    }
    final profile = auth?.profile;
    final canExams = profile?.canSeeExams ?? false;
    final canMaterials = profile?.canSeeMaterials ?? false;
    final canAttendance = profile?.canTakeAttendance ?? false;
    final canSabaq = profile?.canRecordSabaq ?? false;
    final canViewStudents = profile?.canViewStudents ?? false;

    if (data.niLaHifdhu) {
      return _hifdhuView(
        context,
        data,
        canAttendance: canAttendance,
        canViewStudents: canViewStudents,
      );
    }

    final subtitle = [
      'Somo la darasa',
      if (data.darasaJina != null && data.darasaJina!.isNotEmpty)
        data.darasaJina!,
      if (data.mwalimu != null && data.mwalimu!.isNotEmpty)
        'Mwalimu: ${data.mwalimu}',
    ].join(' · ');

    return Stack(
      children: [
        ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          children: [
            AccentCard(
              accent: MadrasaTheme.gold,
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    data.jina,
                    style: const TextStyle(
                      fontFamily: MadrasaTheme.brandFont,
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                      color: MadrasaTheme.title,
                    ),
                  ),
                  if (subtitle.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      subtitle,
                      style: const TextStyle(color: MadrasaTheme.muted),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),
            if (canSabaq || canViewStudents) ...[
              HubCard(
                title: 'Maendeleo ya mchana',
                hint: canSabaq
                    ? 'Rekodi na tazama maendeleo ya wanafunzi kwenye somo hili'
                    : 'Tazama maendeleo ya wanafunzi kwenye somo hili',
                watermarkIcon: Icons.assignment_turned_in_rounded,
                onTap: () => _openMaendeleoSheet(canSabaq: canSabaq),
              ),
              const SizedBox(height: 4),
            ],
            AccentCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Expanded(
                        child: Text(
                          MadrasaCopy.subjectMaterials,
                          style: TextStyle(
                            fontWeight: FontWeight.w800,
                            color: MadrasaTheme.primary,
                            fontSize: 16,
                          ),
                        ),
                      ),
                      if (canMaterials && !data.niLaHifdhu)
                        TextButton.icon(
                          onPressed: _busy ? null : _uploadMaterial,
                          icon: const Icon(Icons.upload_file, size: 18),
                          label: const Text(MadrasaCopy.uploadMaterial),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (data.nyenzo.isEmpty)
                    const Text(
                      MadrasaCopy.noMaterials,
                      style: TextStyle(color: MadrasaTheme.muted),
                    )
                  else
                    ...data.nyenzo.map((item) {
                      final opening = _openingId == item.id;
                      return ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.description_outlined),
                        title: Text(item.jinaLaFaili),
                        subtitle: item.tarehe == null
                            ? null
                            : Text(item.tarehe!.split('T').first),
                        trailing: opening
                            ? const SizedBox(
                                width: 22,
                                height: 22,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : TextButton(
                                onPressed: () => _openMaterial(item),
                                child: const Text(MadrasaCopy.openMaterial),
                              ),
                      );
                    }),
                ],
              ),
            ),
            const SizedBox(height: 16),
            AccentCard(
              accent: MadrasaTheme.primary,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Expanded(
                        child: Text(
                          MadrasaCopy.subjectExams,
                          style: TextStyle(
                            fontWeight: FontWeight.w800,
                            color: MadrasaTheme.primary,
                            fontSize: 16,
                          ),
                        ),
                      ),
                      if (canExams && !data.niLaHifdhu)
                        TextButton.icon(
                          onPressed: _busy ? null : _createExam,
                          icon: const Icon(Icons.add, size: 18),
                          label: const Text(MadrasaCopy.newExam),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (!canExams)
                    const Text(
                      'Huna ruhusa ya kuona mitihani na matokeo.',
                      style: TextStyle(color: MadrasaTheme.muted),
                    )
                  else if (data.mitihani.isEmpty)
                    const Text(
                      MadrasaCopy.noExams,
                      style: TextStyle(color: MadrasaTheme.muted),
                    )
                  else
                    ...data.mitihani.map((exam) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              exam.jina,
                              style: const TextStyle(
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'Tarehe: ${exam.tarehe}',
                              style: const TextStyle(
                                color: MadrasaTheme.muted,
                                fontSize: 13,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Wrap(
                              spacing: 8,
                              children: [
                                OutlinedButton(
                                  onPressed: () => context.push(
                                    '/masomo/${data.id}/mitihani/${exam.id}',
                                    extra: {'edit': false},
                                  ),
                                  child: const Text(MadrasaCopy.viewResults),
                                ),
                                OutlinedButton(
                                  onPressed: () => context.push(
                                    '/masomo/${data.id}/mitihani/${exam.id}',
                                    extra: {'edit': true},
                                  ),
                                  child: const Text(MadrasaCopy.enterMarks),
                                ),
                              ],
                            ),
                          ],
                        ),
                      );
                    }),
                ],
              ),
            ),
          ],
        ),
        if (_busy)
          const ColoredBox(
            color: Color(0x33000000),
            child: Center(child: CircularProgressIndicator()),
          ),
      ],
    );
  }

  Widget _hifdhuView(
    BuildContext context,
    SubjectDetail data, {
    required bool canAttendance,
    required bool canViewStudents,
  }) {
    final wavulana = _hifdhuStudents.where((s) => s.jinsia == 'ME').length;
    final wasichana = _hifdhuStudents.where((s) => s.jinsia == 'KE').length;
    final jumla = _hifdhuStudents.length;

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        Text(
          data.jina,
          style: const TextStyle(
            fontFamily: MadrasaTheme.brandFont,
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: MadrasaTheme.title,
          ),
        ),
        if (data.mwalimu != null && data.mwalimu!.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            'Mwalimu: ${data.mwalimu}',
            style: const TextStyle(color: MadrasaTheme.muted),
          ),
        ],
        const SizedBox(height: 16),
        StudentStatCards(
          wavulana: wavulana,
          wasichana: wasichana,
          jumla: jumla,
        ),
        const SizedBox(height: 20),
        HubCard(
          title: MadrasaCopy.rollCall,
          hint: canAttendance
              ? 'Rekodi yupo / hayupo'
              : MadrasaCopy.viewOnly,
          watermarkIcon: Icons.fact_check_rounded,
          onTap: () => context.push('/masomo/${data.id}/mahudhurio'),
        ),
        HubCard(
          title: 'Rekodi sabaq na murajaa',
          hint: '$jumla wanafunzi (Wanaume: $wavulana · Wanawake: $wasichana)',
          watermarkIcon: Icons.menu_book_rounded,
          onTap: () => context.push('/masomo/${data.id}/wanafunzi'),
        ),
      ],
    );
  }
}

class _MaendeleoMchanaSheet extends StatefulWidget {
  const _MaendeleoMchanaSheet({
    required this.somo,
    required this.repository,
    required this.canSabaq,
  });

  final SubjectDetail somo;
  final CatalogRepository repository;
  final bool canSabaq;

  @override
  State<_MaendeleoMchanaSheet> createState() => _MaendeleoMchanaSheetState();
}

class _MaendeleoMchanaSheetState extends State<_MaendeleoMchanaSheet> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _rows = const [];

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
      _rows = await widget.repository.wanafunziSomoRaw(widget.somo.id);
    } on ApiException catch (e) {
      _error = e.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia wanafunzi.';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _recordProgress(Map<String, dynamic> student) async {
    final madaCtrl = TextEditingController();
    final ukurasaCtrl = TextEditingController();
    final maoniCtrl = TextEditingController();
    String hali = 'Ameelewa';

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: Text('Rekodi Maendeleo: ${student['jina_kamili']}'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: madaCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Mada iliyosomwa',
                    hintText: 'Mf. Mlango wa Udhu',
                  ),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: ukurasaCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Ukurasa au Aya (hiari)',
                    hintText: 'Mf. Uk. 12 - 15',
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Hali ya Uelewa:',
                  style: TextStyle(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8,
                  children: [
                    for (final opt in const [
                      ('Ameelewa', 'Ameelewa'),
                      ('Hajaelewa', 'Hajaelewa'),
                      ('Hajasikilizwa', 'Hajasikilizwa'),
                    ])
                      ChoiceChip(
                        label: Text(opt.$2),
                        selected: hali == opt.$1,
                        onSelected: (v) {
                          if (v) setLocal(() => hali = opt.$1);
                        },
                      ),
                  ],
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: maoniCtrl,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Maoni ya mwalimu (hiari)',
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Ghairi'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Hifadhi'),
            ),
          ],
        ),
      ),
    );

    final mada = madaCtrl.text.trim();
    final ukurasa = ukurasaCtrl.text.trim();
    final maoni = maoniCtrl.text.trim();
    madaCtrl.dispose();
    ukurasaCtrl.dispose();
    maoniCtrl.dispose();

    if (!mounted || ok != true) return;
    if (mada.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Weka mada iliyosomwa.')),
      );
      return;
    }

    try {
      await widget.repository.rekodiMaendeleo(
        mwanafunziId: student['id'] as int,
        somoId: widget.somo.id,
        mada: mada,
        ukurasaAuAya: ukurasa.isEmpty ? null : ukurasa,
        hali: hali,
        maoni: maoni.isEmpty ? null : maoni,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Maendeleo ya mchana yamehifadhiwa.')),
      );
      await _load();
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message)),
        );
      }
    }
  }

  Future<void> _viewStudentMaendeleo(Map<String, dynamic> student) async {
    try {
      final data = await widget.repository.ripotiMaendeleoMchana(
        widget.somo.id,
        student['id'] as int,
      );
      if (!mounted) return;
      final rekodi =
          (data['rekodi'] as List<dynamic>? ?? const [])
              .whereType<Map<String, dynamic>>()
              .toList();
      await showDialog<void>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text('Ripoti: ${student['jina_kamili']}'),
          content: SizedBox(
            width: double.maxFinite,
            child: rekodi.isEmpty
                ? const Text('Hakuna rekodi za maendeleo bado.')
                : ListView.builder(
                    shrinkWrap: true,
                    itemCount: rekodi.length,
                    itemBuilder: (ctx, i) {
                      final r = rekodi[i];
                      return ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: Text('${r['tarehe']} · ${r['mada_iliyosomwa']}'),
                        subtitle: Text(
                          [
                            if ((r['ukurasa_au_aya'] as String?)?.isNotEmpty ==
                                true)
                              'Uk/Aya: ${r['ukurasa_au_aya']}',
                            if ((r['maoni'] as String?)?.isNotEmpty == true)
                              '${r['maoni']}',
                          ].join(' · '),
                        ),
                        trailing: Text(
                          '${r['hali_jina'] ?? r['hali']}',
                          style: const TextStyle(
                            fontWeight: FontWeight.w700,
                            color: MadrasaTheme.primary,
                          ),
                        ),
                      );
                    },
                  ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Funga'),
            ),
          ],
        ),
      );
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message)),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
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
              Text(
                'Maendeleo ya mchana · ${widget.somo.jina}',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: MadrasaTheme.title,
                ),
              ),
              if (widget.somo.darasaJina != null)
                Text(
                  'Darasa: ${widget.somo.darasaJina}',
                  style: const TextStyle(
                    color: MadrasaTheme.muted,
                    fontSize: 13,
                  ),
                ),
              const Divider(height: 20),
              Expanded(
                child: _loading
                    ? const Center(child: CircularProgressIndicator())
                    : _error != null
                    ? Center(child: Text(_error!))
                    : _rows.isEmpty
                    ? const Center(
                        child: Text('Hakuna wanafunzi katika somo hili.'),
                      )
                    : ListView.builder(
                        controller: scrollController,
                        itemCount: _rows.length,
                        itemBuilder: (ctx, i) {
                          final row = _rows[i];
                          final mwisho =
                              row['maendeleo_mwisho'] as Map<String, dynamic>?;
                          return Card(
                            margin: const EdgeInsets.only(bottom: 10),
                            child: Padding(
                              padding: const EdgeInsets.all(12),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          '${row['jina_kamili']}',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.w700,
                                          ),
                                        ),
                                        Text(
                                          '${row['namba_ya_usajili'] ?? ''}',
                                          style: const TextStyle(
                                            fontSize: 12,
                                            color: MadrasaTheme.muted,
                                          ),
                                        ),
                                        if (mwisho != null) ...[
                                          const SizedBox(height: 4),
                                          Text(
                                            'Mwisho (${mwisho['tarehe']}): ${mwisho['mada_iliyosomwa']} · ${mwisho['hali_jina'] ?? mwisho['hali']}',
                                            style: const TextStyle(
                                              fontSize: 12,
                                              color: MadrasaTheme.primary,
                                            ),
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                  if (widget.canSabaq)
                                    FilledButton.tonal(
                                      onPressed: () => _recordProgress(row),
                                      child: const Text('Rekodi'),
                                    ),
                                  const SizedBox(width: 6),
                                  OutlinedButton(
                                    onPressed: () =>
                                        _viewStudentMaendeleo(row),
                                    child: const Text('Ripoti'),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
