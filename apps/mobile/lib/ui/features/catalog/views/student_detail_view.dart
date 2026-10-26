import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';
import 'package:provider/provider.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../../data/services/api_client.dart';
import '../../../../data/services/api_exception.dart';
import '../../../core/copy.dart';
import '../../../core/pdf_downloader.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../../core/widgets/authenticated_photo.dart';
import '../../auth/view_models/auth_view_model.dart';

/// Student profile with the same tabs as the web profile:
/// Muhtasari, Malipo, Mahudhurio, Rekodi.
class StudentDetailView extends StatefulWidget {
  const StudentDetailView({
    super.key,
    required this.studentId,
    required this.repository,
    this.initialTabIndex,
  });

  final int studentId;
  final CatalogRepository repository;
  final int? initialTabIndex;

  @override
  State<StudentDetailView> createState() => _StudentDetailViewState();
}

class _StudentDetailViewState extends State<StudentDetailView> {
  bool _loading = true;
  String? _error;
  StudentOverview? _data;
  int _refreshNonce = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = _data == null;
      _error = null;
    });
    try {
      _data = await widget.repository.mwanafunziMuhtasari(widget.studentId);
      _refreshNonce++;
    } on ApiException catch (error) {
      _error = error.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia taarifa.';
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _downloadRisiti(StudentPayment m) async {
    final malipoId = m.id;
    if (malipoId == null) return;
    final s = _data?.mwanafunzi;
    final filename =
        'Risiti_${s?.nambaYaUsajili ?? widget.studentId}_$malipoId.pdf';
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Inapakua risiti ya PDF...'),
        duration: Duration(seconds: 2),
      ),
    );
    try {
      final bytes = await widget.repository.downloadRisitiPdf(malipoId);
      if (mounted) {
        await PdfDownloader.saveAndOpen(
          context,
          bytes: bytes,
          filename: filename,
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Imeshindikana kupakua risiti: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _downloadMahudhurio(String aina) async {
    final s = _data?.mwanafunzi;
    final filename =
        'Mahudhurio_${aina}_${s?.nambaYaUsajili ?? widget.studentId}.pdf';
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Inapakua PDF ya Mahudhurio ($aina)...'),
        duration: const Duration(seconds: 2),
      ),
    );
    try {
      final bytes = await widget.repository.downloadMahudhurioPdf(
        widget.studentId,
        aina: aina,
      );
      if (mounted) {
        await PdfDownloader.saveAndOpen(
          context,
          bytes: bytes,
          filename: filename,
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Imeshindikana kupakua PDF ya mahudhurio: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _downloadSabaq(String aina) async {
    final s = _data?.mwanafunzi;
    final filename =
        'Sabaq_${aina}_${s?.nambaYaUsajili ?? widget.studentId}.pdf';
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Inapakua PDF ya Sabaq ($aina)...'),
        duration: const Duration(seconds: 2),
      ),
    );
    try {
      final bytes = await widget.repository.downloadSabaqPdf(
        widget.studentId,
        aina: aina,
      );
      if (mounted) {
        await PdfDownloader.saveAndOpen(
          context,
          bytes: bytes,
          filename: filename,
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Imeshindikana kupakua PDF ya sabaq: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _editStudentSheet(StudentDetail s) async {
    Map<String, dynamic> chaguzi = const {};
    try {
      chaguzi = await widget.repository.usajiliChaguzi();
    } catch (_) {}
    if (!mounted) return;
    final madarasa = (chaguzi['madarasa'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();
    final programuUsiku = (chaguzi['programu_usiku'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();

    final jinaCtrl = TextEditingController(text: s.jinaKamili);
    final kuzaliwaCtrl = TextEditingController(text: s.tareheKuzaliwa ?? '');
    final mahalaCtrl = TextEditingController(text: s.mahala ?? '');
    final juzuuCtrl = TextEditingController(
      text: s.juzuu != null ? '${s.juzuu}' : '',
    );
    final mzaziCtrl = TextEditingController(text: s.jinaMzazi ?? '');
    final simuCtrl = TextEditingController(text: s.simuMzazi ?? '');
    final uhusianoCtrl = TextEditingController(text: s.uhusiano ?? '');
    final mzazi2Ctrl = TextEditingController(text: s.jinaMzaziPili ?? '');
    final simu2Ctrl = TextEditingController(text: s.simuMzaziPili ?? '');
    final uhusiano2Ctrl = TextEditingController(text: s.uhusianoPili ?? '');
    String jinsia = s.jinsia == 'KE' ? 'KE' : 'ME';
    int? darasaId = s.darasaId;
    int? programuId = s.programuUsikuId;

    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => Padding(
          padding: EdgeInsets.fromLTRB(
            20,
            8,
            20,
            MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Hariri Mwanafunzi',
                  style: TextStyle(
                    fontFamily: MadrasaTheme.brandFont,
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: MadrasaTheme.title,
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: jinaCtrl,
                  decoration: const InputDecoration(labelText: 'Jina kamili'),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        initialValue: jinsia,
                        decoration: const InputDecoration(labelText: 'Jinsia'),
                        items: const [
                          DropdownMenuItem(
                            value: 'ME',
                            child: Text('Mwanamume (ME)'),
                          ),
                          DropdownMenuItem(
                            value: 'KE',
                            child: Text('Mwanamke (KE)'),
                          ),
                        ],
                        onChanged: (v) {
                          if (v != null) setLocal(() => jinsia = v);
                        },
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: kuzaliwaCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Kuzaliwa (YYYY-MM-DD)',
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                if (madarasa.isNotEmpty) ...[
                  DropdownButtonFormField<int?>(
                    initialValue: madarasa.any((d) => d['id'] == darasaId)
                        ? darasaId
                        : null,
                    decoration: const InputDecoration(labelText: 'Darasa'),
                    items: [
                      const DropdownMenuItem<int?>(
                        value: null,
                        child: Text('— Hakuna darasa —'),
                      ),
                      ...madarasa.map(
                        (d) => DropdownMenuItem<int?>(
                          value: (d['id'] as num?)?.toInt(),
                          child: Text(d['jina']?.toString() ?? '-'),
                        ),
                      ),
                    ],
                    onChanged: (v) => setLocal(() => darasaId = v),
                  ),
                  const SizedBox(height: 10),
                ],
                if (programuUsiku.isNotEmpty) ...[
                  DropdownButtonFormField<int?>(
                    initialValue:
                        programuUsiku.any((p) => p['id'] == programuId)
                            ? programuId
                            : null,
                    decoration: const InputDecoration(
                      labelText: 'Programu ya usiku (Hifdhu)',
                    ),
                    items: [
                      const DropdownMenuItem<int?>(
                        value: null,
                        child: Text('— Hakuna —'),
                      ),
                      ...programuUsiku.map(
                        (p) => DropdownMenuItem<int?>(
                          value: (p['id'] as num?)?.toInt(),
                          child: Text(p['jina']?.toString() ?? '-'),
                        ),
                      ),
                    ],
                    onChanged: (v) => setLocal(() => programuId = v),
                  ),
                  const SizedBox(height: 10),
                ],
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: mahalaCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Mahala anapoishi',
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    SizedBox(
                      width: 110,
                      child: TextField(
                        controller: juzuuCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Juzuu'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: mzaziCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Jina la mzazi (1)',
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: simuCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Simu ya mzazi (1)',
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: uhusianoCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Uhusiano (Baba / Mama / Mlezi)',
                  ),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: mzazi2Ctrl,
                        decoration: const InputDecoration(
                          labelText: 'Jina la mzazi (2 - hiari)',
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: simu2Ctrl,
                        decoration: const InputDecoration(
                          labelText: 'Simu ya mzazi (2 - hiari)',
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: uhusiano2Ctrl,
                  decoration: const InputDecoration(
                    labelText: 'Uhusiano wa mzazi wa 2 (hiari)',
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    TextButton(
                      onPressed: () => Navigator.of(ctx).pop(false),
                      child: const Text('Ghairi'),
                    ),
                    const SizedBox(width: 8),
                    FilledButton(
                      onPressed: () => Navigator.of(ctx).pop(true),
                      child: const Text('Hifadhi'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
    if (saved != true || !mounted) return;
    try {
      await widget.repository.haririMwanafunzi(widget.studentId, {
        'jina_kamili': jinaCtrl.text.trim(),
        'jinsia': jinsia,
        'darasa': darasaId,
        'programu_ya_usiku': programuId,
        'tarehe_ya_kuzaliwa': kuzaliwaCtrl.text.trim().isEmpty
            ? null
            : kuzaliwaCtrl.text.trim(),
        'mahala_anapoishi': mahalaCtrl.text.trim(),
        if (int.tryParse(juzuuCtrl.text.trim()) != null)
          'juzuu_aliyohifadhi': int.parse(juzuuCtrl.text.trim()),
        'jina_la_mzazi': mzaziCtrl.text.trim(),
        'namba_ya_simu_mzazi': simuCtrl.text.trim(),
        'uhusiano_wa_mlezi': uhusianoCtrl.text.trim(),
        'jina_la_mzazi_pili': mzazi2Ctrl.text.trim(),
        'namba_ya_simu_mzazi_pili': simu2Ctrl.text.trim(),
        'uhusiano_wa_mlezi_pili': uhusiano2Ctrl.text.trim(),
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Taarifa za mwanafunzi zimesasishwa.')),
      );
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  Future<void> _toggleArchiveStudent(StudentDetail s) async {
    if (s.amehifadhiwa) {
      final confirm = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Rudisha Mwanafunzi'),
          content: Text(
            'Unataka kumrudisha "${s.jinaKamili}" kwenye orodha ya wanafunzi hai?',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: const Text('Ghairi'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: const Text('Rudisha'),
            ),
          ],
        ),
      );
      if (confirm != true || !mounted) return;
      try {
        await widget.repository.rudishaMwanafunzi(widget.studentId);
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Mwanafunzi amerudishwa kwenye orodha hai.'),
          ),
        );
        await _load();
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
        );
      }
    } else {
      final sababuCtrl = TextEditingController();
      final confirm = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Hifadhi (Archive) Mwanafunzi'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Mwanafunzi "${s.jinaKamili}" ataondolewa kwenye orodha hai lakini historia yake itabaki.',
              ),
              const SizedBox(height: 12),
              TextField(
                controller: sababuCtrl,
                decoration: const InputDecoration(
                  labelText: 'Sababu (mf. Amehama / Amehitimu)',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: const Text('Ghairi'),
            ),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: MadrasaTheme.danger,
              ),
              onPressed: () => Navigator.of(ctx).pop(true),
              child: const Text('Hifadhi'),
            ),
          ],
        ),
      );
      if (confirm != true || !mounted) return;
      try {
        await widget.repository.hifadhiMwanafunzi(
          widget.studentId,
          sababu: sababuCtrl.text.trim(),
        );
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Mwanafunzi amehifadhiwa kwenye kumbukumbu.')),
        );
        await _load();
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
        );
      }
    }
  }

  Future<void> _recordPaymentSheet() async {
    List<Map<String, dynamic>> ainaList = const [];
    try {
      final raw = await widget.repository.ainaMalipoRaw();
      ainaList = (raw['aina'] as List? ?? const [])
          .whereType<Map<String, dynamic>>()
          .toList();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
      return;
    }
    if (!mounted) return;
    if (ainaList.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Tafadhali ongeza Aina ya Malipo kwanza.'),
        ),
      );
      return;
    }
    int selectedAinaId = (ainaList.first['id'] as num).toInt();
    final kiasiCtrl = TextEditingController(
      text: ainaList.first['kiasi_kinachotakiwa']?.toString() ?? '',
    );
    final maelezoCtrl = TextEditingController();
    String njia = 'Cash';

    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => Padding(
          padding: EdgeInsets.fromLTRB(
            20,
            8,
            20,
            MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Weka Malipo: ${_data?.mwanafunzi.jinaKamili ?? ""}',
                  style: const TextStyle(
                    fontFamily: MadrasaTheme.brandFont,
                    fontSize: 19,
                    fontWeight: FontWeight.w700,
                    color: MadrasaTheme.title,
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<int>(
                  initialValue: selectedAinaId,
                  decoration: const InputDecoration(
                    labelText: 'Aina ya malipo',
                  ),
                  items: ainaList
                      .map(
                        (a) => DropdownMenuItem<int>(
                          value: (a['id'] as num).toInt(),
                          child: Text(
                            a['lebo_kamili']?.toString() ??
                                a['jina']?.toString() ??
                                '-',
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (v) {
                    if (v == null) return;
                    setLocal(() {
                      selectedAinaId = v;
                      final match = ainaList.firstWhere(
                        (a) => (a['id'] as num).toInt() == v,
                        orElse: () => const {},
                      );
                      final req = match['kiasi_kinachotakiwa']?.toString();
                      if (req != null && req.isNotEmpty) {
                        kiasiCtrl.text = req;
                      }
                    });
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: kiasiCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(
                    labelText: 'Kiasi kilicholipwa (Tsh)',
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: njia,
                  decoration: const InputDecoration(
                    labelText: 'Njia ya malipo',
                  ),
                  items: const [
                    DropdownMenuItem(value: 'Cash', child: Text('Fedha Taslimu (Cash)')),
                    DropdownMenuItem(value: 'Mobile Money', child: Text('Simu (M-Pesa / TigoPesa / Airtel)')),
                    DropdownMenuItem(value: 'Bank', child: Text('Benki')),
                  ],
                  onChanged: (v) {
                    if (v != null) setLocal(() => njia = v);
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: maelezoCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Maelezo ya ziada (hiari)',
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    TextButton(
                      onPressed: () => Navigator.of(ctx).pop(false),
                      child: const Text('Ghairi'),
                    ),
                    const SizedBox(width: 8),
                    FilledButton(
                      onPressed: () => Navigator.of(ctx).pop(true),
                      child: const Text('Hifadhi Malipo'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
    if (saved != true || !mounted) return;
    final kiasi = kiasiCtrl.text.trim();
    if (kiasi.isEmpty) return;
    try {
      await widget.repository.wekaMalipo(
        mwanafunziId: widget.studentId,
        ainaId: selectedAinaId,
        kiasi: kiasi,
        njia: njia,
        maelezo: maelezoCtrl.text.trim(),
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Malipo yamehifadhiwa kikamilifu!')),
      );
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  Future<void> _openParentContactSheet() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => _StudentParentContactSheet(
        studentId: widget.studentId,
        studentName: _data?.mwanafunzi.jinaKamili ?? '',
        repository: widget.repository,
        onUpdated: _load,
      ),
    );
  }

  Future<void> _recordSabaqForStudent({String defaultAina = 'Darasa'}) async {
    final suraController = TextEditingController();
    final ayaKuanziaController = TextEditingController();
    final ayaKuishiaController = TextEditingController();
    final maoniController = TextEditingController();
    String hali = 'Kajua';
    String aina = defaultAina;
    final mapande = <Map<String, dynamic>>[];

    final ok = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setLocal) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 20,
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.menu_book,
                          color: MadrasaTheme.primary,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Rekodi Sabaq: ${_data?.mwanafunzi.jinaKamili ?? ""}',
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w700,
                              color: MadrasaTheme.title,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        ChoiceChip(
                          label: const Text('Darasa (Mchana)'),
                          selected: aina == 'Darasa',
                          onSelected: (val) {
                            if (val) setLocal(() => aina = 'Darasa');
                          },
                        ),
                        const SizedBox(width: 8),
                        ChoiceChip(
                          label: const Text('Usiku (Hifdhu)'),
                          selected: aina == 'Usiku',
                          onSelected: (val) {
                            if (val) setLocal(() => aina = 'Usiku');
                          },
                        ),
                      ],
                    ),
                    const Divider(height: 24),
                    TextField(
                      controller: suraController,
                      decoration: const InputDecoration(
                        labelText: 'Jina la Sura',
                        hintText: 'Mfano: Al-Baqarah au Juzuu 1',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: ayaKuanziaController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              labelText: 'Aya Kuanzia',
                              border: OutlineInputBorder(),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextField(
                            controller: ayaKuishiaController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              labelText: 'Aya Kuishia',
                              border: OutlineInputBorder(),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Tathmini / Hali ya Sabaq:',
                      style: TextStyle(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      children: ['Kajua', 'Hajajua', 'Hajasikilizwa'].map((
                        opt,
                      ) {
                        final selected = hali == opt;
                        return ChoiceChip(
                          label: Text(opt),
                          selected: selected,
                          selectedColor: opt == 'Kajua'
                              ? MadrasaTheme.successBg
                              : opt == 'Hajajua'
                                  ? MadrasaTheme.dangerBg
                                  : MadrasaTheme.surfaceMuted,
                          onSelected: (val) {
                            if (val) setLocal(() => hali = opt);
                          },
                        );
                      }).toList(),
                    ),
                    if (aina == 'Usiku') ...[
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          const Expanded(
                            child: Text(
                              'Mapande (Murajaa)',
                              style: TextStyle(fontWeight: FontWeight.w700),
                            ),
                          ),
                          TextButton.icon(
                            onPressed: () {
                              setLocal(() {
                                mapande.add({
                                  'sura': TextEditingController(),
                                  'kuanzia': TextEditingController(),
                                  'kuishia': TextEditingController(),
                                  'hali': 'Kajua',
                                });
                              });
                            },
                            icon: const Icon(Icons.add_rounded, size: 18),
                            label: const Text('Ongeza pande'),
                          ),
                        ],
                      ),
                      for (var i = 0; i < mapande.length; i++)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Row(
                            children: [
                              Expanded(
                                flex: 3,
                                child: TextField(
                                  controller:
                                      mapande[i]['sura'] as TextEditingController,
                                  decoration: InputDecoration(
                                    labelText: 'Pande ${i + 1} Sura',
                                    isDense: true,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 6),
                              Expanded(
                                flex: 2,
                                child: TextField(
                                  controller: mapande[i]['kuanzia']
                                      as TextEditingController,
                                  keyboardType: TextInputType.number,
                                  decoration: const InputDecoration(
                                    labelText: 'Kuanzia',
                                    isDense: true,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 6),
                              Expanded(
                                flex: 2,
                                child: TextField(
                                  controller: mapande[i]['kuishia']
                                      as TextEditingController,
                                  keyboardType: TextInputType.number,
                                  decoration: const InputDecoration(
                                    labelText: 'Kuishia',
                                    isDense: true,
                                  ),
                                ),
                              ),
                              IconButton(
                                icon: const Icon(
                                  Icons.close_rounded,
                                  size: 18,
                                  color: MadrasaTheme.danger,
                                ),
                                onPressed: () =>
                                    setLocal(() => mapande.removeAt(i)),
                              ),
                            ],
                          ),
                        ),
                    ],
                    const SizedBox(height: 12),
                    TextField(
                      controller: maoniController,
                      maxLines: 2,
                      decoration: const InputDecoration(
                        labelText: 'Maoni ya Mwalimu (hiari)',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton(
                          onPressed: () => Navigator.pop(context, false),
                          child: const Text('Ghairi'),
                        ),
                        const SizedBox(width: 8),
                        FilledButton(
                          onPressed: () => Navigator.pop(context, true),
                          child: const Text('Hifadhi Sabaq'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );

    if (ok != true) {
      suraController.dispose();
      ayaKuanziaController.dispose();
      ayaKuishiaController.dispose();
      maoniController.dispose();
      return;
    }

    try {
      final mapandePayload = <Map<String, dynamic>>[];
      if (aina == 'Usiku') {
        for (final row in mapande) {
          final sText = (row['sura'] as TextEditingController).text.trim();
          final k1 = int.tryParse(
            (row['kuanzia'] as TextEditingController).text.trim(),
          );
          final k2 = int.tryParse(
            (row['kuishia'] as TextEditingController).text.trim(),
          );
          if (sText.isNotEmpty || k1 != null || k2 != null) {
            mapandePayload.add({
              'sura': sText,
              'kuanzia': k1,
              'kuishia': k2,
              'hali': row['hali'] ?? 'Kajua',
            });
          }
        }
      }
      await widget.repository.rekodiSabaq(
        mwanafunziId: widget.studentId,
        aina: aina,
        sura: suraController.text.trim().isEmpty
            ? null
            : suraController.text.trim(),
        ayaKuanzia: int.tryParse(ayaKuanziaController.text.trim()),
        ayaKuishia: int.tryParse(ayaKuishiaController.text.trim()),
        hali: hali,
        maoni: maoniController.text.trim().isEmpty
            ? null
            : maoniController.text.trim(),
        mapande: mapandePayload.isEmpty ? null : mapandePayload,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Sabaq imerekodiwa kikamilifu!'),
            backgroundColor: MadrasaTheme.primary,
          ),
        );
        _load();
      }
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
      suraController.dispose();
      ayaKuanziaController.dispose();
      ayaKuishiaController.dispose();
      maoniController.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null || _data == null) {
      return _ErrorRetry(message: _error, onRetry: _load);
    }
    final overview = _data!;
    final s = overview.mwanafunzi;
    final jinsia = s.jinsia == 'KE' ? 'Mwanamke (KE)' : 'Mwanamume (ME)';
    final id = widget.studentId;
    final repo = widget.repository;
    AuthViewModel? auth;
    try {
      auth = context.watch<AuthViewModel>();
    } catch (_) {
      auth = null;
    }
    final canSabaq = auth?.profile?.canRecordSabaq ?? false;
    final canManageStudents = auth?.profile?.canManageStudents ?? false;
    final canSeeFees = auth?.profile?.canSeeFees ?? false;
    final canSeeParents = auth?.profile?.canSeeParents ?? false;

    return DefaultTabController(
      length: 4,
      initialIndex: widget.initialTabIndex ?? 0,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: _header(
              context,
              s,
              jinsia,
              canManageStudents: canManageStudents,
            ),
          ),
          const TabBar(
            isScrollable: true,
            tabAlignment: TabAlignment.start,
            labelColor: MadrasaTheme.primary,
            unselectedLabelColor: MadrasaTheme.muted,
            indicatorColor: MadrasaTheme.gold,
            labelStyle: TextStyle(fontWeight: FontWeight.w800),
            tabs: [
              Tab(text: 'Muhtasari'),
              Tab(text: 'Malipo'),
              Tab(text: 'Mahudhurio'),
              Tab(text: 'Rekodi'),
            ],
          ),
          Expanded(
            child: TabBarView(
              children: [
                RefreshIndicator(
                  onRefresh: _load,
                  child: _muhtasari(
                    overview,
                    jinsia,
                    canSeeParents: canSeeParents,
                  ),
                ),
                _TabLoader<StudentPayments>(
                  key: ValueKey('malipo_$_refreshNonce'),
                  load: () => repo.mwanafunziMalipo(id),
                  builder: (data) => _malipo(data, canSeeFees: canSeeFees),
                ),
                _TabLoader<StudentAttendance>(
                  key: ValueKey('mahudhurio_$_refreshNonce'),
                  load: () => repo.mwanafunziMahudhurio(id),
                  builder: _mahudhurio,
                ),
                _TabLoader<StudentRecords>(
                  key: ValueKey('rekodi_$_refreshNonce'),
                  load: () => repo.mwanafunziRekodi(id),
                  builder: (records) => _rekodi(records, canSabaq: canSabaq),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _header(
    BuildContext context,
    StudentDetail s,
    String jinsia, {
    required bool canManageStudents,
  }) {
    final api = context.read<ApiClient>();
    return AccentCard(
      accent: MadrasaTheme.gold,
      padding: const EdgeInsets.all(14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AuthenticatedPhoto(
            api: api,
            url: s.pichaUrl,
            fallbackLabel: s.jinaKamili,
            radius: 30,
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  s.jinaKamili,
                  style: const TextStyle(
                    fontFamily: MadrasaTheme.brandFont,
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: MadrasaTheme.title,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  s.nambaYaUsajili,
                  style: const TextStyle(color: MadrasaTheme.muted),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    _chip(jinsia),
                    if (s.darasa != null) _chip(s.darasa!),
                    if (s.amehifadhiwa)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: MadrasaTheme.dangerBg,
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(color: MadrasaTheme.dangerBorder),
                        ),
                        child: const Text(
                          'Amehifadhiwa',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: MadrasaTheme.dangerText,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
          if (canManageStudents)
            Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  tooltip: 'Hariri mwanafunzi',
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(
                    Icons.edit_outlined,
                    color: MadrasaTheme.primary,
                    size: 20,
                  ),
                  onPressed: () => _editStudentSheet(s),
                ),
                IconButton(
                  tooltip: s.amehifadhiwa
                      ? 'Rudisha mwanafunzi'
                      : 'Hifadhi (Archive)',
                  visualDensity: VisualDensity.compact,
                  icon: Icon(
                    s.amehifadhiwa
                        ? Icons.restore_rounded
                        : Icons.archive_outlined,
                    color: s.amehifadhiwa
                        ? MadrasaTheme.successText
                        : MadrasaTheme.danger,
                    size: 20,
                  ),
                  onPressed: () => _toggleArchiveStudent(s),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _muhtasari(
    StudentOverview o,
    String jinsia, {
    required bool canSeeParents,
  }) {
    final s = o.mwanafunzi;
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            final width = (constraints.maxWidth - 12) / 2;
            Widget tile(String label, String value) =>
                SizedBox(width: width, child: _SummaryTile(label, value));
            return Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                tile('Malipo Yote', 'Tsh ${_money(o.jumlaMalipo)}'),
                tile('Mahudhurio ya Mchana', '${o.mahudhurioMchana}'),
                tile('Mahudhurio ya Hifdhu', '${o.mahudhurioHifdhu}'),
                tile('Rekodi za Sabaq', '${o.idadiSabaq}'),
                tile('Maendeleo ya mchana', '${o.idadiMaendeleo}'),
              ],
            );
          },
        ),
        const SizedBox(height: 16),
        _section('Taarifa za msingi', [
          _kv('Darasa', s.darasa),
          _kv('Jinsia', jinsia),
          _kv('Tarehe ya kuzaliwa', s.tareheKuzaliwa),
          _kv('Mahala', s.mahala),
          _kv('Tarehe ya kujiunga', s.tareheKujiunga),
        ]),
        if (s.programuUsiku != null || s.juzuu != null) ...[
          const SizedBox(height: 12),
          _section('Hifdhu / usiku', [
            _kv('Programu ya usiku', s.programuUsiku),
            _kv('Juzuu', s.juzuu?.toString()),
          ]),
        ],
        if (s.jinaMzazi != null || s.simuMzazi != null || canSeeParents) ...[
          const SizedBox(height: 12),
          _section(
            'Mzazi / mlezi',
            [
              _kv('Jina', s.jinaMzazi),
              _kv('Uhusiano', s.uhusiano),
              _kv('Simu', s.simuMzazi),
              _kv('Jina (pili)', s.jinaMzaziPili),
              _kv('Uhusiano (pili)', s.uhusianoPili),
              _kv('Simu (pili)', s.simuMzaziPili),
            ],
            action: canSeeParents
                ? OutlinedButton.icon(
                    onPressed: _openParentContactSheet,
                    icon: const Icon(Icons.phone_in_talk_outlined, size: 16),
                    label: const Text('Simu / WhatsApp'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 0,
                      ),
                      visualDensity: VisualDensity.compact,
                    ),
                  )
                : null,
          ),
        ],
      ],
    );
  }

  Widget _malipo(StudentPayments data, {required bool canSeeFees}) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      children: [
        if (canSeeFees) ...[
          AccentCard(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                const Icon(
                  Icons.payments_outlined,
                  color: MadrasaTheme.primary,
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Rekodi Malipo Mapya ya Ada',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: MadrasaTheme.title,
                    ),
                  ),
                ),
                FilledButton.tonalIcon(
                  onPressed: _recordPaymentSheet,
                  icon: const Icon(Icons.add, size: 16),
                  label: const Text('Weka Malipo'),
                  style: FilledButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
        ],
        _SummaryTile('Jumla ya malipo', 'Tsh ${_money(data.jumla)}'),
        const SizedBox(height: 12),
        _section('Historia ya Malipo', [
          if (data.malipo.isEmpty)
            _empty('Mwanafunzi huyu bado hajasajiliwa kuwa na malipo yoyote.'),
          for (final m in data.malipo)
            _row(
              title: m.aina,
              subtitle: [
                _date(m.tarehe),
                if (m.njia != null && m.njia!.isNotEmpty) m.njia!,
                m.alirekodi ?? '—',
              ].join(' · '),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '${_money(m.kiasi)}/=',
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      color: MadrasaTheme.successText,
                    ),
                  ),
                  if (m.id != null) ...[
                    const SizedBox(width: 4),
                    IconButton(
                      icon: const Icon(
                        Icons.picture_as_pdf_outlined,
                        color: MadrasaTheme.primary,
                        size: 20,
                      ),
                      tooltip: 'Pakua Risiti',
                      onPressed: () => _downloadRisiti(m),
                    ),
                  ],
                ],
              ),
            ),
        ]),
      ],
    );
  }

  Widget _mahudhurio(StudentAttendance data) {
    List<Widget> rows(List<StudentAttendanceDay> days, String empty) => [
      if (days.isEmpty) _empty(empty),
      for (final d in days)
        _row(title: _date(d.tarehe), trailing: _status(d.yupo)),
    ];
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      children: [
        _section(
          'Mahudhurio ya Madrasa',
          rows(data.kawaida, 'Hakuna rekodi za mahudhurio ya Madrasa.'),
          action: OutlinedButton.icon(
            onPressed: () => _downloadMahudhurio('Darasa'),
            icon: const Icon(Icons.picture_as_pdf_outlined, size: 16),
            label: const Text('Pakua PDF'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
              visualDensity: VisualDensity.compact,
            ),
          ),
        ),
        const SizedBox(height: 12),
        _section(
          'Mahudhurio ya Hifdhu',
          rows(data.hifdhu, 'Hakuna rekodi za mahudhurio ya Hifdhu.'),
          action: OutlinedButton.icon(
            onPressed: () => _downloadMahudhurio('Usiku'),
            icon: const Icon(Icons.picture_as_pdf_outlined, size: 16),
            label: const Text('Pakua PDF'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
              visualDensity: VisualDensity.compact,
            ),
          ),
        ),
      ],
    );
  }

  Widget _rekodi(StudentRecords data, {required bool canSabaq}) {
    List<Widget> rows(List<StudentRecord> list, String empty) => [
      if (list.isEmpty) _empty(empty),
      for (final r in list)
        _row(
          title: '${_date(r.tarehe)} - ${r.kichwa}',
          subtitle: r.maelezo,
          trailing: Text(
            r.hali,
            style: const TextStyle(
              fontWeight: FontWeight.w700,
              color: MadrasaTheme.primary,
            ),
          ),
        ),
    ];
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      children: [
        if (canSabaq) ...[
          AccentCard(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                const Icon(Icons.menu_book, color: MadrasaTheme.primary),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Kurekodi Maendeleo / Sabaq',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: MadrasaTheme.title,
                    ),
                  ),
                ),
                FilledButton.tonalIcon(
                  onPressed: () => _recordSabaqForStudent(),
                  icon: const Icon(Icons.add, size: 16),
                  label: const Text('Rekodi Sabaq'),
                  style: FilledButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
        ],
        _section(
          'Sabaq ya Darasa',
          rows(data.sabaqDarasa, 'Hakuna rekodi za sabaq ya darasa.'),
          action: OutlinedButton.icon(
            onPressed: () => _downloadSabaq('Darasa'),
            icon: const Icon(Icons.picture_as_pdf_outlined, size: 16),
            label: const Text('Pakua PDF'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
              visualDensity: VisualDensity.compact,
            ),
          ),
        ),
        const SizedBox(height: 12),
        _section(
          'Sabaq ya Usiku',
          rows(data.sabaqUsiku, 'Hakuna rekodi za sabaq ya usiku.'),
          action: OutlinedButton.icon(
            onPressed: () => _downloadSabaq('Usiku'),
            icon: const Icon(Icons.picture_as_pdf_outlined, size: 16),
            label: const Text('Pakua PDF'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
              visualDensity: VisualDensity.compact,
            ),
          ),
        ),
        const SizedBox(height: 12),
        _section(
          'Maendeleo ya mchana',
          rows(data.maendeleo, 'Hakuna maendeleo ya mchana bado.'),
        ),
      ],
    );
  }

  static String _money(String raw) {
    final value = double.tryParse(raw);
    if (value == null) {
      return raw;
    }
    return NumberFormat('#,##0').format(value);
  }

  static String _date(String iso) {
    final parsed = DateTime.tryParse(iso);
    return parsed == null ? iso : DateFormat('d MMM y').format(parsed);
  }

  Widget _status(bool yupo) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(
        color: yupo ? MadrasaTheme.successBg : MadrasaTheme.dangerBg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(
          color: yupo ? MadrasaTheme.successBorder : MadrasaTheme.dangerBorder,
        ),
      ),
      child: Text(
        yupo ? MadrasaCopy.present : MadrasaCopy.absent,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: yupo ? MadrasaTheme.successText : MadrasaTheme.dangerText,
        ),
      ),
    );
  }

  Widget _row({required String title, String? subtitle, Widget? trailing}) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: MadrasaTheme.border)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: MadrasaTheme.ink,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (subtitle != null && subtitle.isNotEmpty) ...[
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      color: MadrasaTheme.muted,
                      fontSize: 12,
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (trailing != null) ...[const SizedBox(width: 10), trailing],
        ],
      ),
    );
  }

  Widget _empty(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Text(text, style: const TextStyle(color: MadrasaTheme.muted)),
    );
  }

  Widget _chip(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: MadrasaTheme.successBg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: MadrasaTheme.successBorder),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: MadrasaTheme.successText,
        ),
      ),
    );
  }

  Widget _section(String title, List<Widget> kids, {Widget? action}) {
    final visible = kids.whereType<Widget>().toList();
    return AccentCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    color: MadrasaTheme.primary,
                    fontSize: 16,
                  ),
                ),
              ),
              if (action != null) action,
            ],
          ),
          const SizedBox(height: 10),
          ...visible,
        ],
      ),
    );
  }

  Widget _kv(String label, String? value) {
    if (value == null || value.isEmpty) {
      return const SizedBox.shrink();
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(
                color: MadrasaTheme.muted,
                fontWeight: FontWeight.w600,
                fontSize: 13,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: MadrasaTheme.ink,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StudentParentContactSheet extends StatefulWidget {
  const _StudentParentContactSheet({
    required this.studentId,
    required this.studentName,
    required this.repository,
    required this.onUpdated,
  });

  final int studentId;
  final String studentName;
  final CatalogRepository repository;
  final VoidCallback onUpdated;

  @override
  State<_StudentParentContactSheet> createState() =>
      _StudentParentContactSheetState();
}

class _StudentParentContactSheetState
    extends State<_StudentParentContactSheet> {
  Future<Map<String, dynamic>>? _future;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    setState(() {
      _future = widget.repository.mawasilianoDetail(widget.studentId);
    });
  }

  Future<void> _logCallDialog() async {
    String aina = 'Kawaida';
    String matokeo = 'Amepokea';
    final maelezoCtrl = TextEditingController();
    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: const Text('Rekodi Simu kwa Mzazi'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<String>(
                  initialValue: aina,
                  decoration: const InputDecoration(labelText: 'Aina ya simu'),
                  items: const [
                    DropdownMenuItem(value: 'Kawaida', child: Text('Simu ya Kawaida')),
                    DropdownMenuItem(value: 'WhatsApp', child: Text('WhatsApp')),
                    DropdownMenuItem(value: 'SMS', child: Text('Ujumbe wa SMS')),
                  ],
                  onChanged: (v) {
                    if (v != null) setLocal(() => aina = v);
                  },
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  initialValue: matokeo,
                  decoration: const InputDecoration(labelText: 'Matokeo'),
                  items: const [
                    DropdownMenuItem(value: 'Amepokea', child: Text('Amepokea')),
                    DropdownMenuItem(value: 'Hajapokea', child: Text('Hajapokea')),
                    DropdownMenuItem(value: 'Haipatikani', child: Text('Namba haipatikani')),
                    DropdownMenuItem(value: 'Ujumbe umetumwa', child: Text('Ujumbe umetumwa')),
                  ],
                  onChanged: (v) {
                    if (v != null) setLocal(() => matokeo = v);
                  },
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: maelezoCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Muhtasari wa mazungumzo',
                  ),
                  maxLines: 2,
                ),
              ],
            ),
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
      ),
    );
    if (saved != true || !mounted) return;
    try {
      await widget.repository.rekodiSimu(widget.studentId, {
        'aina_ya_simu': aina,
        'matokeo': matokeo,
        'maelezo': maelezoCtrl.text.trim(),
      });
      if (!mounted) return;
      _reload();
      widget.onUpdated();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Simu imerekodiwa kikamilifu.')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  Future<void> _openWhatsApp({int mzaziSlot = 1}) async {
    final msgCtrl = TextEditingController(
      text:
          'Assalamu Alaykum mzazi wa ${widget.studentName}, tunawasiliana kutoka Madrasatul Rasulillah.',
    );
    final send = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Fungua WhatsApp'),
        content: TextField(
          controller: msgCtrl,
          decoration: const InputDecoration(labelText: 'Ujumbe wa WhatsApp'),
          maxLines: 3,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Ghairi'),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.of(ctx).pop(true),
            icon: const Icon(Icons.chat_outlined, size: 18),
            label: const Text('Fungua WhatsApp'),
          ),
        ],
      ),
    );
    if (send != true || !mounted) return;
    try {
      final urlStr = await widget.repository.funguaWhatsApp(
        widget.studentId,
        ujumbe: msgCtrl.text.trim(),
        mzazi: mzaziSlot,
      );
      if (urlStr.isNotEmpty) {
        await Clipboard.setData(ClipboardData(text: urlStr));
        try {
          await OpenFilex.open(urlStr);
        } catch (_) {}
      }
      if (!mounted) return;
      _reload();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Kiungo cha WhatsApp kimefunguliwa / kimenakiliwa.'),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
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
                        'Mawasiliano na Mzazi',
                        style: TextStyle(
                          fontFamily: MadrasaTheme.brandFont,
                          fontSize: 19,
                          fontWeight: FontWeight.w700,
                          color: MadrasaTheme.title,
                        ),
                      ),
                      Text(
                        widget.studentName,
                        style: const TextStyle(
                          color: MadrasaTheme.muted,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
                FilledButton.tonalIcon(
                  onPressed: _logCallDialog,
                  icon: const Icon(Icons.add_call, size: 16),
                  label: const Text('Rekodi Simu'),
                ),
                const SizedBox(width: 6),
                FilledButton.icon(
                  onPressed: () => _openWhatsApp(),
                  icon: const Icon(Icons.chat_outlined, size: 16),
                  label: const Text('WhatsApp'),
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
                  final logs = (data['historia_simu'] as List? ??
                          data['simu'] as List? ??
                          const [])
                      .whereType<Map<String, dynamic>>()
                      .toList();
                  if (logs.isEmpty) {
                    return const Center(
                      child: Text(
                        'Hakuna rekodi za simu au mawasiliano bado.',
                        style: TextStyle(color: MadrasaTheme.muted),
                      ),
                    );
                  }
                  return ListView.separated(
                    controller: scrollController,
                    itemCount: logs.length,
                    separatorBuilder: (c, idx) => const SizedBox(height: 8),
                    itemBuilder: (ctx, i) {
                      final l = logs[i];
                      final aina = l['aina']?.toString() ??
                          l['aina_ya_simu']?.toString() ??
                          '-';
                      final matokeo = l['matokeo']?.toString() ?? '-';
                      final maelezo = l['maelezo']?.toString() ?? '';
                      final tarehe = l['tarehe']?.toString() ?? '';
                      final mwalimu = l['mwalimu']?.toString() ?? '';
                      return Card(
                        margin: EdgeInsets.zero,
                        child: ListTile(
                          leading: const CircleAvatar(
                            backgroundColor: MadrasaTheme.outlineSoft,
                            foregroundColor: MadrasaTheme.maroon,
                            child: Icon(Icons.phone_callback_outlined, size: 18),
                          ),
                          title: Text(
                            '$aina · $matokeo',
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          subtitle: Text(
                            [
                              if (maelezo.isNotEmpty) maelezo,
                              if (mwalimu.isNotEmpty) 'Na: $mwalimu',
                              if (tarehe.isNotEmpty) tarehe,
                            ].join(' · '),
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

class _SummaryTile extends StatelessWidget {
  const _SummaryTile(this.label, this.value);

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return AccentCard(
      padding: const EdgeInsets.fromLTRB(14, 12, 12, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: MadrasaTheme.muted,
              fontWeight: FontWeight.w600,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: const TextStyle(
              color: MadrasaTheme.title,
              fontWeight: FontWeight.w800,
              fontSize: 20,
            ),
          ),
        ],
      ),
    );
  }
}

/// Loads a tab's data the first time it is shown and keeps it while the
/// user switches tabs; pull down to reload.
class _TabLoader<T> extends StatefulWidget {
  const _TabLoader({super.key, required this.load, required this.builder});

  final Future<T> Function() load;
  final Widget Function(T data) builder;

  @override
  State<_TabLoader<T>> createState() => _TabLoaderState<T>();
}

class _TabLoaderState<T> extends State<_TabLoader<T>>
    with AutomaticKeepAliveClientMixin {
  bool _loading = true;
  String? _error;
  T? _data;

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = _data == null;
      _error = null;
    });
    try {
      final data = await widget.load();
      _data = data;
    } on ApiException catch (error) {
      _error = error.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia taarifa.';
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    final data = _data;
    if (data == null) {
      return _ErrorRetry(message: _error, onRetry: _load);
    }
    return RefreshIndicator(onRefresh: _load, child: widget.builder(data));
  }
}

class _ErrorRetry extends StatelessWidget {
  const _ErrorRetry({required this.message, required this.onRetry});

  final String? message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message ?? MadrasaCopy.emptyList, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: onRetry,
              child: const Text(MadrasaCopy.retry),
            ),
          ],
        ),
      ),
    );
  }
}
