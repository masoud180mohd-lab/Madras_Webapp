import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../../data/services/api_client.dart';
import '../../../../data/services/api_exception.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../../core/widgets/authenticated_photo.dart';

/// Student profile with the same tabs as the web profile:
/// Muhtasari, Malipo, Mahudhurio, Rekodi.
class StudentDetailView extends StatefulWidget {
  const StudentDetailView({
    super.key,
    required this.studentId,
    required this.repository,
  });

  final int studentId;
  final CatalogRepository repository;

  @override
  State<StudentDetailView> createState() => _StudentDetailViewState();
}

class _StudentDetailViewState extends State<StudentDetailView> {
  bool _loading = true;
  String? _error;
  StudentOverview? _data;

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
    return DefaultTabController(
      length: 4,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: _header(context, s, jinsia),
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
                  child: _muhtasari(overview, jinsia),
                ),
                _TabLoader<StudentPayments>(
                  load: () => repo.mwanafunziMalipo(id),
                  builder: _malipo,
                ),
                _TabLoader<StudentAttendance>(
                  load: () => repo.mwanafunziMahudhurio(id),
                  builder: _mahudhurio,
                ),
                _TabLoader<StudentRecords>(
                  load: () => repo.mwanafunziRekodi(id),
                  builder: _rekodi,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _header(BuildContext context, StudentDetail s, String jinsia) {
    final api = context.read<ApiClient>();
    return AccentCard(
      accent: MadrasaTheme.gold,
      padding: const EdgeInsets.all(14),
      child: Row(
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
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _muhtasari(StudentOverview o, String jinsia) {
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
        if (s.jinaMzazi != null || s.simuMzazi != null) ...[
          const SizedBox(height: 12),
          _section('Mzazi / mlezi', [
            _kv('Jina', s.jinaMzazi),
            _kv('Uhusiano', s.uhusiano),
            _kv('Simu', s.simuMzazi),
            _kv('Jina (pili)', s.jinaMzaziPili),
            _kv('Uhusiano (pili)', s.uhusianoPili),
            _kv('Simu (pili)', s.simuMzaziPili),
          ]),
        ],
      ],
    );
  }

  Widget _malipo(StudentPayments data) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      children: [
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
              trailing: Text(
                '${_money(m.kiasi)}/=',
                style: const TextStyle(
                  fontWeight: FontWeight.w800,
                  color: MadrasaTheme.successText,
                ),
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
        ),
        const SizedBox(height: 12),
        _section(
          'Mahudhurio ya Hifdhu',
          rows(data.hifdhu, 'Hakuna rekodi za mahudhurio ya Hifdhu.'),
        ),
      ],
    );
  }

  Widget _rekodi(StudentRecords data) {
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
        _section(
          'Sabaq ya Darasa',
          rows(data.sabaqDarasa, 'Hakuna rekodi za sabaq ya darasa.'),
        ),
        const SizedBox(height: 12),
        _section(
          'Sabaq ya Usiku',
          rows(data.sabaqUsiku, 'Hakuna rekodi za sabaq ya usiku.'),
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

  Widget _section(String title, List<Widget> kids) {
    final visible = kids.whereType<Widget>().toList();
    return AccentCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontWeight: FontWeight.w800,
              color: MadrasaTheme.primary,
              fontSize: 16,
            ),
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
  const _TabLoader({required this.load, required this.builder});

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
