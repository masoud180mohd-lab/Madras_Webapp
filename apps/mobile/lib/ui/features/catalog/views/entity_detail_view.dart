import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../data/models/models.dart';
import '../../../../data/services/api_client.dart';
import '../../../../data/services/api_exception.dart';
import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/accent_card.dart';
import '../../../core/widgets/authenticated_photo.dart';

class EntityDetailView extends StatefulWidget {
  const EntityDetailView({
    super.key,
    required this.loader,
    this.heading = 'Maelezo',
  });

  final Future<CatalogRow> Function() loader;
  final String heading;

  @override
  State<EntityDetailView> createState() => _EntityDetailViewState();
}

class _EntityDetailViewState extends State<EntityDetailView> {
  bool _loading = true;
  String? _error;
  CatalogRow? _row;

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
      _row = await widget.loader();
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
    if (_error != null || _row == null) {
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
    final row = _row!;
    final api = context.read<ApiClient>();
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
                url: row.photoUrl,
                fallbackLabel: row.title,
                radius: 36,
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      row.title,
                      style: const TextStyle(
                        fontFamily: MadrasaTheme.brandFont,
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: MadrasaTheme.title,
                      ),
                    ),
                    if (row.subtitle != null) ...[
                      const SizedBox(height: 6),
                      Text(
                        row.subtitle!,
                        style: const TextStyle(color: MadrasaTheme.muted),
                      ),
                    ],
                    if (row.badge != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        row.badge!,
                        style: const TextStyle(
                          color: MadrasaTheme.successText,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
        if (row.trailing != null) ...[
          const SizedBox(height: 12),
          AccentCard(
            child: Text(
              row.trailing!,
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                color: MadrasaTheme.gold,
              ),
            ),
          ),
        ],
      ],
    );
  }
}
