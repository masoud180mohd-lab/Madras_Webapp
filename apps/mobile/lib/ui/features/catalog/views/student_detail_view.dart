import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../../data/services/api_client.dart';
import '../../../../data/services/api_exception.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../../core/widgets/authenticated_photo.dart';

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
  StudentDetail? _data;

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
      _data = await widget.repository.mwanafunziDetail(widget.studentId);
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
    final s = _data!;
    final api = context.read<ApiClient>();
    final jinsia = s.jinsia == 'KE' ? 'Mwanamke (KE)' : 'Mwanamume (ME)';
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        AccentCard(
          accent: MadrasaTheme.gold,
          padding: const EdgeInsets.all(18),
          child: Row(
            children: [
              AuthenticatedPhoto(
                api: api,
                url: s.pichaUrl,
                fallbackLabel: s.jinaKamili,
                radius: 36,
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
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: MadrasaTheme.title,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      s.nambaYaUsajili,
                      style: const TextStyle(color: MadrasaTheme.muted),
                    ),
                    const SizedBox(height: 8),
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
