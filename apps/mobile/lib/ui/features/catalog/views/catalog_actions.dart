import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:open_filex/open_filex.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../core/copy.dart';
import '../../../core/pdf_downloader.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';

class CatalogActions {
  const CatalogActions._();

  // ---------------- WANAFUNZI ----------------
  static Widget wanafunziTopBar({
    required BuildContext context,
    required CatalogRepository repo,
    required bool canRegister,
    required String currentHali,
    required ValueChanged<String> onSelectHali,
    required VoidCallback reload,
  }) {
    return Row(
      children: [
        Expanded(
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                for (final entry in const [
                  ('hai', 'Hai'),
                  ('hifadhiwa', 'Waliohifadhiwa'),
                  ('wote', 'Wote'),
                ])
                  Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: ChoiceChip(
                      label: Text(entry.$2),
                      selected: currentHali == entry.$1,
                      onSelected: (v) {
                        if (v) onSelectHali(entry.$1);
                      },
                    ),
                  ),
              ],
            ),
          ),
        ),
        if (canRegister) ...[
          const SizedBox(width: 8),
          FilledButton.icon(
            onPressed: () =>
                showRegisterStudentSheet(context, repo: repo, onSaved: reload),
            icon: const Icon(Icons.person_add_alt_1_rounded, size: 18),
            label: const Text('Sajili'),
          ),
        ],
      ],
    );
  }

  static Future<void> showRegisterStudentSheet(
    BuildContext context, {
    required CatalogRepository repo,
    required VoidCallback onSaved,
  }) async {
    Map<String, dynamic> chaguzi = const {};
    try {
      chaguzi = await repo.usajiliChaguzi();
    } catch (_) {}
    if (!context.mounted) return;
    final madarasa = (chaguzi['madarasa'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();
    final programuUsiku = (chaguzi['programu_usiku'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();

    final jinaCtrl = TextEditingController();
    final kuzaliwaCtrl = TextEditingController();
    final mahalaCtrl = TextEditingController();
    final juzuuCtrl = TextEditingController(text: '0');
    final mzaziCtrl = TextEditingController();
    final simuCtrl = TextEditingController();
    final uhusianoCtrl = TextEditingController(text: 'Baba');
    String jinsia = 'ME';
    int? darasaId = madarasa.isNotEmpty
        ? (madarasa.first['id'] as num?)?.toInt()
        : null;
    int? programuId;

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
                  'Sajili Mwanafunzi Mpya',
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
                    initialValue: darasaId,
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
                    initialValue: programuId,
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
                      width: 100,
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
                          labelText: 'Jina la mzazi / mlezi',
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: simuCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Simu ya mzazi',
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
                      child: const Text('Sajili Mwanafunzi'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
    if (saved != true || !context.mounted) return;
    final jina = jinaCtrl.text.trim();
    if (jina.isEmpty) return;
    try {
      await repo.sajiliMwanafunzi({
        'jina_kamili': jina,
        'jinsia': jinsia,
        'darasa': darasaId,
        'programu_ya_usiku': programuId,
        if (kuzaliwaCtrl.text.trim().isNotEmpty)
          'tarehe_ya_kuzaliwa': kuzaliwaCtrl.text.trim(),
        'mahala_anapoishi': mahalaCtrl.text.trim(),
        'juzuu_aliyohifadhi': int.tryParse(juzuuCtrl.text.trim()) ?? 0,
        'jina_la_mzazi': mzaziCtrl.text.trim(),
        'namba_ya_simu_mzazi': simuCtrl.text.trim(),
        'uhusiano_wa_mlezi': uhusianoCtrl.text.trim(),
      });
      if (!context.mounted) return;
      onSaved();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Mwanafunzi amesajiliwa kikamilifu!')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  // ---------------- WALIMU ----------------
  static Widget walimuTopBar({
    required BuildContext context,
    required CatalogRepository repo,
    required VoidCallback reload,
  }) {
    return Align(
      alignment: Alignment.centerRight,
      child: FilledButton.icon(
        onPressed: () =>
            showRegisterTeacherSheet(context, repo: repo, onSaved: reload),
        icon: const Icon(Icons.person_add_alt_1_rounded, size: 18),
        label: const Text('Ongeza Mwalimu'),
      ),
    );
  }

  static Future<void> showRegisterTeacherSheet(
    BuildContext context, {
    required CatalogRepository repo,
    required VoidCallback onSaved,
  }) async {
    final usernameCtrl = TextEditingController();
    final passCtrl = TextEditingController();
    final firstNameCtrl = TextEditingController();
    final lastNameCtrl = TextEditingController();
    final simuCtrl = TextEditingController();
    String cheo = 'Mwalimu wa Kawaida';

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
                  'Ongeza Mwalimu Mpya',
                  style: TextStyle(
                    fontFamily: MadrasaTheme.brandFont,
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: MadrasaTheme.title,
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: firstNameCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Jina la kwanza',
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: lastNameCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Jina la ukoo',
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: usernameCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Username ya kuingia',
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: passCtrl,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'Nenosiri (Password)',
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  initialValue: cheo,
                  decoration: const InputDecoration(labelText: 'Cheo'),
                  items: const [
                    DropdownMenuItem(
                      value: 'Mwalimu wa Kawaida',
                      child: Text('Mwalimu wa Kawaida'),
                    ),
                    DropdownMenuItem(
                      value: 'Mwalimu Mkuu',
                      child: Text('Mwalimu Mkuu'),
                    ),
                    DropdownMenuItem(
                      value: 'Katibu',
                      child: Text('Katibu'),
                    ),
                    DropdownMenuItem(
                      value: 'Jaji',
                      child: Text('Jaji'),
                    ),
                  ],
                  onChanged: (v) {
                    if (v != null) setLocal(() => cheo = v.trim());
                  },
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: simuCtrl,
                  decoration: const InputDecoration(labelText: 'Namba ya simu'),
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
                      child: const Text('Sajili Mwalimu'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
    if (saved != true || !context.mounted) return;
    try {
      await repo.sajiliMwalimu({
        'username': usernameCtrl.text.trim(),
        'password': passCtrl.text,
        'first_name': firstNameCtrl.text.trim(),
        'last_name': lastNameCtrl.text.trim(),
        'cheo': cheo,
        'namba_ya_simu': simuCtrl.text.trim(),
      });
      if (!context.mounted) return;
      onSaved();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Mwalimu amesajiliwa kikamilifu!')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  static Future<void> showEditTeacherDialog(
    BuildContext context, {
    required int mwalimuId,
    required CatalogRepository repo,
    required VoidCallback onSaved,
  }) async {
    Map<String, dynamic> detail = const {};
    try {
      detail = await repo.mwalimuDetailRaw(mwalimuId);
    } catch (_) {}
    if (!context.mounted) return;
    final jinaParts = (detail['jina']?.toString() ?? '').split(' ');
    final firstNameCtrl = TextEditingController(
      text: jinaParts.isNotEmpty ? jinaParts.first : '',
    );
    final lastNameCtrl = TextEditingController(
      text: jinaParts.length > 1 ? jinaParts.sublist(1).join(' ') : '',
    );
    final simuCtrl = TextEditingController(
      text: detail['namba_ya_simu']?.toString() ?? '',
    );
    final passCtrl = TextEditingController();
    String cheo = detail['cheo']?.toString() ?? 'Mwalimu wa Kawaida';
    const cheoOpts = ['Mwalimu wa Kawaida', 'Mwalimu Mkuu', 'Katibu', 'Jaji'];
    if (!cheoOpts.contains(cheo)) {
      cheo = 'Mwalimu wa Kawaida';
    }

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: const Text('Hariri Mwalimu'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: firstNameCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Jina la kwanza',
                  ),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: lastNameCtrl,
                  decoration: const InputDecoration(labelText: 'Jina la ukoo'),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  initialValue: cheo,
                  decoration: const InputDecoration(labelText: 'Cheo'),
                  items: cheoOpts
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (v) {
                    if (v != null) setLocal(() => cheo = v);
                  },
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: simuCtrl,
                  decoration: const InputDecoration(labelText: 'Namba ya simu'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: passCtrl,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Badilisha nenosiri (hiari)',
                  ),
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
    if (saved != true || !context.mounted) return;
    try {
      await repo.haririMwalimu(mwalimuId, {
        'first_name': firstNameCtrl.text.trim(),
        'last_name': lastNameCtrl.text.trim(),
        'cheo': cheo,
        'namba_ya_simu': simuCtrl.text.trim(),
        if (passCtrl.text.isNotEmpty) 'new_password': passCtrl.text,
      });
      if (!context.mounted) return;
      onSaved();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Taarifa za mwalimu zimesasishwa.')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  // ---------------- MASOMO ----------------
  static Widget masomoTopBar({
    required BuildContext context,
    required CatalogRepository repo,
    required VoidCallback reload,
  }) {
    return Align(
      alignment: Alignment.centerRight,
      child: FilledButton.icon(
        onPressed: () =>
            showCreateSubjectDialog(context, repo: repo, onSaved: reload),
        icon: const Icon(Icons.add_rounded, size: 18),
        label: const Text('Ongeza Somo'),
      ),
    );
  }

  static Future<void> showCreateSubjectDialog(
    BuildContext context, {
    required CatalogRepository repo,
    required VoidCallback onSaved,
  }) async {
    Map<String, dynamic> chaguzi = const {};
    try {
      chaguzi = await repo.usajiliChaguzi();
    } catch (_) {}
    if (!context.mounted) return;
    final madarasa = (chaguzi['madarasa'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();
    final walimu = (chaguzi['walimu'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();

    final jinaCtrl = TextEditingController();
    int? darasaId;
    int? mwalimuId;
    bool niLaHifdhu = false;

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: const Text('Ongeza Somo Jipya'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: jinaCtrl,
                  decoration: const InputDecoration(labelText: 'Jina la somo'),
                ),
                const SizedBox(height: 10),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Somo la Usiku / Hifdhu'),
                  value: niLaHifdhu,
                  onChanged: (v) => setLocal(() => niLaHifdhu = v),
                ),
                if (!niLaHifdhu && madarasa.isNotEmpty) ...[
                  DropdownButtonFormField<int?>(
                    initialValue: darasaId,
                    decoration: const InputDecoration(labelText: 'Darasa'),
                    items: [
                      const DropdownMenuItem<int?>(
                        value: null,
                        child: Text('— Chagua darasa —'),
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
                if (walimu.isNotEmpty)
                  DropdownButtonFormField<int?>(
                    initialValue: mwalimuId,
                    decoration: const InputDecoration(
                      labelText: 'Mwalimu (hiari)',
                    ),
                    items: [
                      const DropdownMenuItem<int?>(
                        value: null,
                        child: Text('— Hakuna —'),
                      ),
                      ...walimu.map(
                        (w) => DropdownMenuItem<int?>(
                          value: (w['id'] as num?)?.toInt(),
                          child: Text(w['jina']?.toString() ?? '-'),
                        ),
                      ),
                    ],
                    onChanged: (v) => setLocal(() => mwalimuId = v),
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
    if (saved != true || !context.mounted) return;
    final jina = jinaCtrl.text.trim();
    if (jina.isEmpty) return;
    try {
      await repo.sajiliSomo({
        'jina': jina,
        'darasa': niLaHifdhu ? null : darasaId,
        'mwalimu': mwalimuId,
        'ni_la_hifdhu': niLaHifdhu,
      });
      if (!context.mounted) return;
      onSaved();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Somo limeongezwa kikamilifu.')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  // ---------------- MALIPO ----------------
  static Future<void> onMalipoRowTap(
    BuildContext context,
    CatalogRow row, {
    required CatalogRepository repo,
  }) async {
    final id = row.id;
    if (id == null) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Inapakua risiti ya PDF...'),
        duration: Duration(seconds: 2),
      ),
    );
    try {
      final bytes = await repo.downloadRisitiPdf(id);
      if (context.mounted) {
        await PdfDownloader.saveAndOpen(
          context,
          bytes: bytes,
          filename: 'Risiti_$id.pdf',
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
        );
      }
    }
  }

  // ---------------- AINA YA MALIPO ----------------
  static Widget ainaMalipoTopBar({
    required BuildContext context,
    required CatalogRepository repo,
    required VoidCallback reload,
  }) {
    return Align(
      alignment: Alignment.centerRight,
      child: FilledButton.icon(
        onPressed: () =>
            showAinaMalipoDialog(context, repo: repo, onSaved: reload),
        icon: const Icon(Icons.add_rounded, size: 18),
        label: const Text('Ongeza Aina ya Ada'),
      ),
    );
  }

  static Future<void> showAinaMalipoDialog(
    BuildContext context, {
    required CatalogRepository repo,
    required VoidCallback onSaved,
    CatalogRow? existing,
  }) async {
    final jinaCtrl = TextEditingController(text: existing?.title ?? '');
    final kiasiCtrl = TextEditingController(
      text: existing?.trailing
              ?.replaceAll('Tsh', '')
              .replaceAll(',', '')
              .trim() ??
          '',
    );
    final maelezoCtrl = TextEditingController();

    final action = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(
          existing == null ? 'Ongeza Aina ya Ada' : 'Hariri Aina ya Ada',
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: jinaCtrl,
              decoration: const InputDecoration(
                labelText: 'Jina la ada (mf. Ada ya Mwezi)',
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: kiasiCtrl,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(
                labelText: 'Kiasi kinachotakiwa (Tsh)',
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: maelezoCtrl,
              decoration: const InputDecoration(labelText: 'Maelezo (hiari)'),
            ),
          ],
        ),
        actions: [
          if (existing?.id != null)
            TextButton(
              style: TextButton.styleFrom(foregroundColor: MadrasaTheme.danger),
              onPressed: () => Navigator.of(ctx).pop('delete'),
              child: const Text('Futa'),
            ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop('cancel'),
            child: const Text('Ghairi'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop('save'),
            child: const Text('Hifadhi'),
          ),
        ],
      ),
    );
    if (!context.mounted) return;
    if (action == 'delete' && existing?.id != null) {
      try {
        await repo.futaAinaMalipo(existing!.id!);
        if (!context.mounted) return;
        onSaved();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Aina ya ada imefutwa.')),
        );
      } catch (e) {
        if (!context.mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
        );
      }
      return;
    }
    if (action != 'save') return;
    final jina = jinaCtrl.text.trim();
    final kiasi = kiasiCtrl.text.trim();
    if (jina.isEmpty || kiasi.isEmpty) return;
    try {
      final body = {
        'jina': jina,
        'kiasi_kinachotakiwa': kiasi,
        'maelezo': maelezoCtrl.text.trim(),
      };
      if (existing?.id != null) {
        await repo.haririAinaMalipo(existing!.id!, body);
      } else {
        await repo.undaAinaMalipo(body);
      }
      if (!context.mounted) return;
      onSaved();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Aina ya ada imehifadhiwa.')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  // ---------------- MWAKA & MUHULA ----------------
  static Widget mwakaTopBar({
    required BuildContext context,
    required CatalogRepository repo,
    required VoidCallback reload,
  }) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      alignment: WrapAlignment.end,
      children: [
        OutlinedButton.icon(
          onPressed: () =>
              showCreateMuhulaDialog(context, repo: repo, onSaved: reload),
          icon: const Icon(Icons.calendar_view_month_rounded, size: 18),
          label: const Text('Ongeza Muhula'),
        ),
        FilledButton.icon(
          onPressed: () =>
              showCreateMwakaDialog(context, repo: repo, onSaved: reload),
          icon: const Icon(Icons.add_rounded, size: 18),
          label: const Text('Ongeza Mwaka'),
        ),
      ],
    );
  }

  static Future<void> showCreateMwakaDialog(
    BuildContext context, {
    required CatalogRepository repo,
    required VoidCallback onSaved,
  }) async {
    final nowYear = DateTime.now().year;
    final kuanziaCtrl = TextEditingController(text: '$nowYear');
    final kuishaCtrl = TextEditingController(text: '${nowYear + 1}');
    final jinaCtrl = TextEditingController(text: '$nowYear/${nowYear + 1}');
    bool niHai = true;

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: const Text('Ongeza Mwaka wa Masomo'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: jinaCtrl,
                decoration: const InputDecoration(
                  labelText: 'Jina la mwaka (mf. 2026/2027)',
                ),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: kuanziaCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Mwaka kuanzia',
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextField(
                      controller: kuishaCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Mwaka kuisha',
                      ),
                    ),
                  ),
                ],
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Weka kuwa Mwaka Hai'),
                value: niHai,
                onChanged: (v) => setLocal(() => niHai = v),
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
      ),
    );
    if (saved != true || !context.mounted) return;
    final k1 = int.tryParse(kuanziaCtrl.text.trim());
    final k2 = int.tryParse(kuishaCtrl.text.trim());
    if (k1 == null || k2 == null) return;
    try {
      await repo.undaMwaka({
        'jina': jinaCtrl.text.trim(),
        'mwaka_kuanzia': k1,
        'mwaka_kuisha': k2,
        'ni_hai': niHai,
      });
      if (!context.mounted) return;
      onSaved();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Mwaka wa masomo umeongezwa.')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  static Future<void> showCreateMuhulaDialog(
    BuildContext context, {
    required CatalogRepository repo,
    required VoidCallback onSaved,
  }) async {
    List<Map<String, dynamic>> miaka = const [];
    try {
      final raw = await repo.mwakaRaw();
      miaka = (raw['miaka'] as List? ?? const [])
          .whereType<Map<String, dynamic>>()
          .toList();
    } catch (_) {}
    if (!context.mounted) return;
    if (miaka.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ongeza Mwaka wa Masomo kwanza.')),
      );
      return;
    }
    int mwakaId = (miaka.first['id'] as num).toInt();
    int namba = 1;
    final jinaCtrl = TextEditingController(text: 'Muhula wa 1');
    bool niHai = true;

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: const Text('Ongeza Muhula'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<int>(
                initialValue: mwakaId,
                decoration: const InputDecoration(
                  labelText: 'Mwaka wa masomo',
                ),
                items: miaka
                    .map(
                      (m) => DropdownMenuItem<int>(
                        value: (m['id'] as num).toInt(),
                        child: Text(m['jina']?.toString() ?? '-'),
                      ),
                    )
                    .toList(),
                onChanged: (v) {
                  if (v != null) setLocal(() => mwakaId = v);
                },
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<int>(
                initialValue: namba,
                decoration: const InputDecoration(labelText: 'Namba ya muhula'),
                items: const [
                  DropdownMenuItem(value: 1, child: Text('Muhula wa 1')),
                  DropdownMenuItem(value: 2, child: Text('Muhula wa 2')),
                  DropdownMenuItem(value: 3, child: Text('Muhula wa 3')),
                ],
                onChanged: (v) {
                  if (v != null) {
                    setLocal(() {
                      namba = v;
                      jinaCtrl.text = 'Muhula wa $v';
                    });
                  }
                },
              ),
              const SizedBox(height: 10),
              TextField(
                controller: jinaCtrl,
                decoration: const InputDecoration(labelText: 'Jina la muhula'),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Weka kuwa Muhula Hai'),
                value: niHai,
                onChanged: (v) => setLocal(() => niHai = v),
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
      ),
    );
    if (saved != true || !context.mounted) return;
    try {
      await repo.undaMuhula({
        'mwaka': mwakaId,
        'namba': namba,
        'jina': jinaCtrl.text.trim(),
        'ni_hai': niHai,
      });
      if (!context.mounted) return;
      onSaved();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Muhula umeongezwa.')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  static Future<void> onMwakaRowTap(
    BuildContext context,
    CatalogRow row, {
    required CatalogRepository repo,
    required VoidCallback reload,
  }) async {
    final id = row.id;
    if (id == null) return;
    final isMuhula = row.subtitle?.startsWith('Muhula ') ?? false;
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(isMuhula ? 'Wezesha Muhula' : 'Wezesha Mwaka wa Masomo'),
        content: Text(
          'Unataka kuweka "${row.title}" kuwa ${isMuhula ? "muhula hai" : "mwaka hai wa masomo"}?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Ghairi'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Wezesha'),
          ),
        ],
      ),
    );
    if (confirm != true || !context.mounted) return;
    try {
      if (isMuhula) {
        await repo.wezeshaMuhula(id);
      } else {
        await repo.wezeshaMwaka(id);
      }
      if (!context.mounted) return;
      reload();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Imesasishwa kuwa hai!')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  // ---------------- HAMISHA DARASA ----------------
  static Widget hamishaTopBar({
    required BuildContext context,
    required CatalogRepository repo,
    required VoidCallback reload,
  }) {
    return AccentCard(
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          const Icon(Icons.upgrade_rounded, color: MadrasaTheme.primary),
          const SizedBox(width: 10),
          const Expanded(
            child: Text(
              'Hamisha wanafunzi wote wa darasa moja kwenda darasa jingine.',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
            ),
          ),
          FilledButton.icon(
            onPressed: () =>
                showPromoteClassDialog(context, repo: repo, onSaved: reload),
            icon: const Icon(Icons.swap_horiz_rounded, size: 18),
            label: const Text('Hamisha'),
          ),
        ],
      ),
    );
  }

  static Future<void> showPromoteClassDialog(
    BuildContext context, {
    required CatalogRepository repo,
    required VoidCallback onSaved,
  }) async {
    Map<String, dynamic> chaguzi = const {};
    try {
      chaguzi = await repo.usajiliChaguzi();
    } catch (_) {}
    if (!context.mounted) return;
    final madarasa = (chaguzi['madarasa'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();
    if (madarasa.length < 2) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Kunahitajika angalau madarasa mawili ili kuhamisha.'),
        ),
      );
      return;
    }
    int kutokaId = (madarasa.first['id'] as num).toInt();
    int kwendaId = (madarasa[1]['id'] as num).toInt();

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: const Text('Hamisha Wanafunzi wa Darasa'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<int>(
                initialValue: kutokaId,
                decoration: const InputDecoration(
                  labelText: 'Kutoka Darasa',
                ),
                items: madarasa
                    .map(
                      (d) => DropdownMenuItem<int>(
                        value: (d['id'] as num).toInt(),
                        child: Text(d['jina']?.toString() ?? '-'),
                      ),
                    )
                    .toList(),
                onChanged: (v) {
                  if (v != null) setLocal(() => kutokaId = v);
                },
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<int>(
                initialValue: kwendaId,
                decoration: const InputDecoration(
                  labelText: 'Kwenda Darasa',
                ),
                items: madarasa
                    .map(
                      (d) => DropdownMenuItem<int>(
                        value: (d['id'] as num).toInt(),
                        child: Text(d['jina']?.toString() ?? '-'),
                      ),
                    )
                    .toList(),
                onChanged: (v) {
                  if (v != null) setLocal(() => kwendaId = v);
                },
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
              child: const Text('Hamisha Sasa'),
            ),
          ],
        ),
      ),
    );
    if (saved != true || !context.mounted) return;
    try {
      final rows = await repo.wanafunzi(darasa: '$kutokaId');
      final ids = rows.map((r) => r.id).whereType<int>().toList();
      final res = await repo.hamishaDarasa(
        kutokaId: kutokaId,
        kwendaId: kwendaId,
        wanafunziIds: ids,
      );
      if (!context.mounted) return;
      onSaved();
      final count = res['waliohamishwa'] ?? ids.length;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Wanafunzi $count wamehamishwa kikamilifu!')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(MadrasaCopy.humanizeError(e))),
      );
    }
  }

  // ---------------- MAWASILIANO / WHATSAPP ----------------
  static Widget mawasilianoTopBar({
    required BuildContext context,
    required CatalogRepository repo,
  }) {
    return Align(
      alignment: Alignment.centerRight,
      child: FilledButton.icon(
        onPressed: () => showWhatsAppCampaignSheet(context, repo: repo),
        icon: const Icon(Icons.chat_outlined, size: 18),
        label: const Text('Kampeni ya WhatsApp'),
      ),
    );
  }

  static Future<void> showWhatsAppCampaignSheet(
    BuildContext context, {
    required CatalogRepository repo,
  }) async {
    Map<String, dynamic> chaguzi = const {};
    try {
      chaguzi = await repo.usajiliChaguzi();
    } catch (_) {}
    if (!context.mounted) return;
    final madarasa = (chaguzi['madarasa'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .toList();
    String walengwa = 'wote';
    int? darasaId = madarasa.isNotEmpty
        ? (madarasa.first['id'] as num?)?.toInt()
        : null;
    final ujumbeCtrl = TextEditingController(
      text:
          'Assalamu Alaykum mzazi wa {mwanafunzi}, tunapenda kukumbusha taarifa muhimu kutoka Madrasatul Rasulillah.',
    );

    final res = await showModalBottomSheet<Map<String, dynamic>>(
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
                  'Tuma Ujumbe wa WhatsApp kwa Wazazi',
                  style: TextStyle(
                    fontFamily: MadrasaTheme.brandFont,
                    fontSize: 19,
                    fontWeight: FontWeight.w700,
                    color: MadrasaTheme.title,
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: walengwa,
                  decoration: const InputDecoration(labelText: 'Walengwa'),
                  items: const [
                    DropdownMenuItem(
                      value: 'wote',
                      child: Text('Wazazi Wote'),
                    ),
                    DropdownMenuItem(
                      value: 'darasa',
                      child: Text('Darasa Maalum'),
                    ),
                    DropdownMenuItem(
                      value: 'wadaiwa',
                      child: Text('Wadaiwa wa Ada'),
                    ),
                  ],
                  onChanged: (v) {
                    if (v != null) setLocal(() => walengwa = v);
                  },
                ),
                if (walengwa == 'darasa' && madarasa.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  DropdownButtonFormField<int?>(
                    initialValue: darasaId,
                    decoration: const InputDecoration(labelText: 'Darasa'),
                    items: madarasa
                        .map(
                          (d) => DropdownMenuItem<int?>(
                            value: (d['id'] as num?)?.toInt(),
                            child: Text(d['jina']?.toString() ?? '-'),
                          ),
                        )
                        .toList(),
                    onChanged: (v) => setLocal(() => darasaId = v),
                  ),
                ],
                const SizedBox(height: 10),
                TextField(
                  controller: ujumbeCtrl,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Ujumbe (tumia {mwanafunzi} kuweka jina)',
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    TextButton(
                      onPressed: () => Navigator.of(ctx).pop(),
                      child: const Text('Ghairi'),
                    ),
                    const SizedBox(width: 8),
                    FilledButton.icon(
                      onPressed: () async {
                        try {
                          final data = await repo.whatsappKampeni(
                            kigezo: walengwa,
                            ujumbe: ujumbeCtrl.text.trim(),
                            darasa: walengwa == 'darasa' && darasaId != null
                                ? '$darasaId'
                                : null,
                          );
                          if (ctx.mounted) Navigator.of(ctx).pop(data);
                        } catch (e) {
                          if (ctx.mounted) {
                            ScaffoldMessenger.of(ctx).showSnackBar(
                              SnackBar(
                                content: Text(MadrasaCopy.humanizeError(e)),
                              ),
                            );
                          }
                        }
                      },
                      icon: const Icon(Icons.send_rounded, size: 16),
                      label: const Text('Andaa Viungo'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
    if (res == null || !context.mounted) return;
    final viungo = (res['viungo'] as List? ??
            res['wanafunzi'] as List? ??
            const [])
        .whereType<Map<String, dynamic>>()
        .toList();
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.7,
        builder: (ctx, sc) => Padding(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Viungo vya WhatsApp (${viungo.length})',
                style: const TextStyle(
                  fontFamily: MadrasaTheme.brandFont,
                  fontSize: 19,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Expanded(
                child: viungo.isEmpty
                    ? const Center(
                        child: Text(
                          'Hakuna wazazi wenye namba za simu kwa kundi hili.',
                        ),
                      )
                    : ListView.separated(
                        controller: sc,
                        itemCount: viungo.length,
                        separatorBuilder: (c, idx) => const SizedBox(height: 8),
                        itemBuilder: (ctx, i) {
                          final item = viungo[i];
                          final jina =
                              item['jina_kamili']?.toString() ??
                              item['mwanafunzi']?.toString() ??
                              '-';
                          final simu = item['simu']?.toString() ?? '';
                          final url = item['whatsapp_url']?.toString() ??
                              item['wa_url']?.toString() ??
                              item['url']?.toString() ??
                              '';
                          return Card(
                            margin: EdgeInsets.zero,
                            child: ListTile(
                              title: Text(jina),
                              subtitle: Text(simu),
                              trailing: FilledButton.tonalIcon(
                                onPressed: () async {
                                  if (url.isNotEmpty) {
                                    await Clipboard.setData(
                                      ClipboardData(text: url),
                                    );
                                    try {
                                      await OpenFilex.open(url);
                                    } catch (_) {}
                                    if (ctx.mounted) {
                                      ScaffoldMessenger.of(ctx).showSnackBar(
                                        const SnackBar(
                                          content: Text(
                                            'Kiungo cha WhatsApp kimefunguliwa / kimenakiliwa.',
                                          ),
                                        ),
                                      );
                                    }
                                  }
                                },
                                icon: const Icon(Icons.chat_outlined, size: 16),
                                label: const Text('Fungua'),
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  static Future<void> onMawasilianoRowTap(
    BuildContext context,
    CatalogRow row,
  ) async {
    if (row.id != null) {
      context.push('/wanafunzi/${row.id}');
    }
  }
}
