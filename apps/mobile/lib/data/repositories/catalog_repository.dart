import '../models/models.dart';
import '../services/api_client.dart';

class CatalogRepository {
  CatalogRepository({required ApiClient api}) : _api = api;

  final ApiClient _api;

  Future<DashboardSnapshot> mwanzo() async {
    final raw = await _api.get('/api/v1/mwanzo/');
    return DashboardSnapshot.fromJson(raw as Map<String, dynamic>);
  }

  Future<List<CatalogRow>> walimu() async {
    final list = await _api.get('/api/v1/walimu/') as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      final cheo = row['cheo'] as String?;
      return CatalogRow(
        title: row['jina'] as String? ?? row['username'] as String? ?? '',
        subtitle: cheo,
        trailing: row['namba_ya_simu'] as String?,
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> wanafunzi({String? q, String? darasa}) async {
    final query = <String, String>{};
    if (q != null && q.isNotEmpty) {
      query['q'] = q;
    }
    if (darasa != null && darasa.isNotEmpty) {
      query['darasa'] = darasa;
    }
    final list =
        await _api.get(
              '/api/v1/wanafunzi/',
              query: query.isEmpty ? null : query,
            )
            as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      final darasa = row['darasa'] as String?;
      final namba = row['namba_ya_usajili'] as String?;
      return CatalogRow(
        title: row['jina_kamili'] as String? ?? '',
        subtitle: [
          if (namba != null && namba.isNotEmpty) namba,
          if (darasa != null && darasa.isNotEmpty) darasa,
        ].join(' · '),
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> masomo() async {
    final list = await _api.get('/api/v1/masomo/') as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      final hifdhu = row['ni_la_hifdhu'] == true;
      return CatalogRow(
        title: row['jina'] as String? ?? '',
        subtitle: hifdhu ? 'Somo la hifdhu' : 'Somo la darasa',
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> watoro() async {
    final raw = await _api.get('/api/v1/watoro/') as Map<String, dynamic>;
    final rows = <CatalogRow>[];
    void addGroup(String label, dynamic items) {
      if (items is! List) {
        return;
      }
      for (final item in items.whereType<Map<String, dynamic>>()) {
        final count = item['idadi_ya_utoro'];
        rows.add(
          CatalogRow(
            title: item['jina_kamili'] as String? ?? '',
            subtitle: [
              label,
              if (item['darasa'] != null) item['darasa'] as String,
            ].join(' · '),
            trailing: count == null ? null : '$count',
          ),
        );
      }
    }

    addGroup('Chuoni', raw['chuoni']);
    addGroup('Darsa', raw['darsa']);
    return rows;
  }

  Future<List<CatalogRow>> malipo() async {
    final list = await _api.get('/api/v1/malipo/') as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      return CatalogRow(
        title: row['mwanafunzi'] as String? ?? '',
        subtitle: [
          row['aina'] as String? ?? '',
          row['tarehe_ya_malipo'] as String? ?? '',
        ].join(' · '),
        trailing: '${row['kiasi_kilicholipwa']}',
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> ainaMalipo() async {
    final list = await _api.get('/api/v1/aina-malipo/') as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      return CatalogRow(
        title: row['lebo_kamili'] as String? ?? row['jina'] as String? ?? '',
        subtitle: row['mwaka'] as String?,
        trailing: '${row['kiasi_kinachotakiwa']}',
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> mwaka() async {
    final list = await _api.get('/api/v1/mwaka/') as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      final hai = row['ni_hai'] == true;
      final muhula = row['muhula'];
      String? subtitle;
      if (muhula is List && muhula.isNotEmpty) {
        subtitle = muhula
            .whereType<Map<String, dynamic>>()
            .map((item) {
              final name = item['jina'] as String? ?? 'Muhula ${item['namba']}';
              return item['ni_hai'] == true ? '$name (hai)' : name;
            })
            .join(', ');
      }
      return CatalogRow(
        title: row['jina'] as String? ?? '',
        subtitle: subtitle,
        trailing: hai ? 'Hai' : null,
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> hamisha() async {
    final list = await _api.get('/api/v1/hamisha/') as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      return CatalogRow(
        title: row['jina'] as String? ?? '',
        trailing: '${row['idadi_wanafunzi'] ?? 0} wanafunzi',
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> mawasiliano({String? q}) async {
    final list =
        await _api.get(
              '/api/v1/mawasiliano/',
              query: q == null || q.isEmpty ? null : {'q': q},
            )
            as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      final simu = row['namba_ya_simu_mzazi'] as String?;
      final mzazi = row['jina_la_mzazi'] as String?;
      return CatalogRow(
        title: row['jina_kamili'] as String? ?? '',
        subtitle: [
          if (row['darasa'] != null) row['darasa'] as String,
          if (mzazi != null && mzazi.isNotEmpty) mzazi,
        ].join(' · '),
        trailing: simu,
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> ukaguzi() async {
    final list = await _api.get('/api/v1/ukaguzi/') as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      return CatalogRow(
        title: row['kitendo_jina'] as String? ?? row['kitendo'] as String? ?? '',
        subtitle: row['maelezo'] as String?,
        trailing: row['mtumiaji'] as String?,
      );
    }).toList(growable: false);
  }
}
