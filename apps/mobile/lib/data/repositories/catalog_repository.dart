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
      final id = row['id'] as int?;
      return CatalogRow(
        id: id,
        title: row['jina'] as String? ?? row['username'] as String? ?? '',
        subtitle: [
          if (row['cheo'] != null) row['cheo'] as String,
          if ((row['namba_ya_simu'] as String?)?.isNotEmpty == true)
            row['namba_ya_simu'] as String,
        ].join(' · '),
        photoUrl: row['picha'] as String?,
        detailPath: id == null ? null : '/walimu/$id',
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
      final id = row['id'] as int?;
      final jinsia = row['jinsia'] as String?;
      return CatalogRow(
        id: id,
        title: row['jina_kamili'] as String? ?? '',
        subtitle: [
          if ((row['namba_ya_usajili'] as String?)?.isNotEmpty == true)
            row['namba_ya_usajili'] as String,
          if ((row['darasa'] as String?)?.isNotEmpty == true)
            row['darasa'] as String,
        ].join(' · '),
        photoUrl: row['picha'] as String?,
        badge: jinsia == 'KE'
            ? 'KE'
            : jinsia == 'ME'
            ? 'ME'
            : null,
        detailPath: id == null ? null : '/wanafunzi/$id',
      );
    }).toList(growable: false);
  }

  Future<StudentDetail> mwanafunziDetail(int id) async {
    final raw = await _api.get('/api/v1/wanafunzi/$id/');
    return StudentDetail.fromJson(raw as Map<String, dynamic>);
  }

  Future<SubjectDetail> somoDetail(int id) async {
    final raw = await _api.get('/api/v1/masomo/$id/');
    return SubjectDetail.fromJson(raw as Map<String, dynamic>);
  }

  Future<ExamResults> matokeo(int mtihaniId) async {
    final raw = await _api.get('/api/v1/mitihani/$mtihaniId/matokeo/');
    return ExamResults.fromJson(raw as Map<String, dynamic>);
  }

  Future<void> hifadhiMaksi(int mtihaniId, List<Map<String, dynamic>> rekodi) {
    return _api.put(
      '/api/v1/mitihani/$mtihaniId/matokeo/',
      body: {'rekodi': rekodi},
    );
  }

  Future<SubjectMaterial> pakiaNyenzo({
    required int somoId,
    required String jinaLaFaili,
    required List<int> bytes,
    required String filename,
  }) async {
    final raw = await _api.postMultipart(
      '/api/v1/masomo/$somoId/nyenzo/',
      fields: {'jina_la_faili': jinaLaFaili},
      fileField: 'faili',
      bytes: bytes,
      filename: filename,
    );
    return SubjectMaterial.fromJson(raw as Map<String, dynamic>);
  }

  Future<SubjectExam> undaMtihani({
    required int somoId,
    required String jina,
    required String tarehe,
  }) async {
    final raw = await _api.post(
      '/api/v1/masomo/$somoId/mitihani/',
      body: {
        'jina_la_mtihani': jina,
        'tarehe': tarehe,
      },
    );
    return SubjectExam.fromJson(raw as Map<String, dynamic>);
  }

  Future<List<CatalogRow>> masomo() async {
    final list = await _api.get('/api/v1/masomo/') as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      final hifdhu = row['ni_la_hifdhu'] == true;
      final darasa = row['darasa_jina'] as String?;
      final mwalimu = row['mwalimu'] as String?;
      return CatalogRow(
        id: row['id'] as int?,
        title: row['jina'] as String? ?? '',
        subtitle: [
          if (hifdhu) 'Hifdhu (usiku)' else 'Somo la darasa',
          if (darasa != null && darasa.isNotEmpty) darasa,
          if (mwalimu != null && mwalimu.isNotEmpty) mwalimu,
        ].join(' · '),
        badge: hifdhu ? 'Usiku' : 'Mchana',
        detailPath: row['id'] == null ? null : '/masomo/${row['id']}',
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> watoro() async {
    final raw = await _api.get('/api/v1/watoro/') as Map<String, dynamic>;
    final rows = <CatalogRow>[];

    void addSection(String title, String maelezo, dynamic items) {
      rows.add(
        CatalogRow(title: title, subtitle: maelezo, isHeader: true),
      );
      if (items is! List || items.isEmpty) {
        rows.add(
          const CatalogRow(
            title: 'Hakuna watoro katika sehemu hii.',
            subtitle: null,
          ),
        );
        return;
      }
      for (final item in items.whereType<Map<String, dynamic>>()) {
        final count = item['idadi_ya_utoro'];
        final id = item['id'] as int?;
        rows.add(
          CatalogRow(
            id: id,
            title: item['jina_kamili'] as String? ?? '',
            subtitle: [
              item['aina_jina'] as String? ?? title,
              if (item['darasa'] != null) item['darasa'] as String,
            ].join(' · '),
            trailing: count == null ? null : '$count siku',
            badge: item['aina'] == 'usiku' ? 'Usiku' : 'Mchana',
            detailPath: id == null ? null : '/wanafunzi/$id',
          ),
        );
      }
    }

    addSection(
      'Kawaida (mchana)',
      'Utoro wa madrasa ya kawaida',
      raw['chuoni'],
    );
    addSection(
      'Usiku (hifdhu)',
      'Utoro wa darsa ya usiku',
      raw['darsa'],
    );
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
          if (row['njia_ya_malipo'] != null) row['njia_ya_malipo'] as String,
        ].join(' · '),
        trailing: 'Tsh ${row['kiasi_kilicholipwa']}',
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> ainaMalipo() async {
    final list = await _api.get('/api/v1/aina-malipo/') as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      return CatalogRow(
        title: row['lebo_kamili'] as String? ?? row['jina'] as String? ?? '',
        subtitle: [
          if (row['mwaka'] != null) row['mwaka'] as String,
          if (row['mwezi'] != null) 'Mwezi ${row['mwezi']}',
        ].join(' · '),
        trailing: 'Tsh ${row['kiasi_kinachotakiwa']}',
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
        badge: hai ? 'Hai' : null,
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
      final id = row['id'] as int?;
      final simu = row['namba_ya_simu_mzazi'] as String?;
      final mzazi = row['jina_la_mzazi'] as String?;
      return CatalogRow(
        id: id,
        title: row['jina_kamili'] as String? ?? '',
        subtitle: [
          if (row['darasa'] != null) row['darasa'] as String,
          if (mzazi != null && mzazi.isNotEmpty) mzazi,
          if ((row['uhusiano_wa_mlezi'] as String?)?.isNotEmpty == true)
            row['uhusiano_wa_mlezi'] as String,
        ].join(' · '),
        trailing: simu,
        detailPath: id == null ? null : '/wanafunzi/$id',
      );
    }).toList(growable: false);
  }

  Future<List<CatalogRow>> ukaguzi() async {
    final list = await _api.get('/api/v1/ukaguzi/') as List<dynamic>;
    return list.whereType<Map<String, dynamic>>().map((row) {
      return CatalogRow(
        title: row['kitendo_jina'] as String? ?? row['kitendo'] as String? ?? '',
        subtitle: [
          if (row['maelezo'] != null) row['maelezo'] as String,
          if (row['tarehe_ya_kitendo'] != null)
            (row['tarehe_ya_kitendo'] as String).split('T').first,
        ].join(' · '),
        trailing: row['mtumiaji'] as String?,
      );
    }).toList(growable: false);
  }
}
