import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../../data/services/api_client.dart';
import '../../../../data/services/api_exception.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
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
  String? _error;
  SubjectDetail? _data;
  int? _openingId;

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
      _data = await widget.repository.somoDetail(widget.somoId);
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
    final canExams = context.watch<AuthViewModel>().profile?.canSeeExams ?? false;
    final subtitle = [
      if (data.niLaHifdhu) 'Hifdhu (usiku)' else 'Somo la darasa',
      if (data.darasaJina != null && data.darasaJina!.isNotEmpty) data.darasaJina!,
      if (data.mwalimu != null && data.mwalimu!.isNotEmpty)
        'Mwalimu: ${data.mwalimu}',
    ].join(' · ');

    return ListView(
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
        AccentCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                MadrasaCopy.subjectMaterials,
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: MadrasaTheme.primary,
                  fontSize: 16,
                ),
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
                            child: CircularProgressIndicator(strokeWidth: 2),
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
              const Text(
                MadrasaCopy.subjectExams,
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: MadrasaTheme.primary,
                  fontSize: 16,
                ),
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
                          style: const TextStyle(fontWeight: FontWeight.w700),
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
    );
  }
}
