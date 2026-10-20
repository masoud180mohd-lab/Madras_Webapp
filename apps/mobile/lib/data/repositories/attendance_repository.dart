import '../models/models.dart';
import '../services/api_client.dart';
import '../services/api_exception.dart';

class AttendanceRepository {
  AttendanceRepository({required ApiClient api}) : _api = api;

  final ApiClient _api;

  Future<List<Darasa>> listMadarasa() async {
    final raw = await _api.get('/api/v1/madarasa/');
    final list = raw as List<dynamic>;
    return list
        .map((row) => Darasa.fromJson(row as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<List<Mwanafunzi>> roster(int darasaId) =>
      _roster('/api/v1/madarasa/$darasaId/wanafunzi/');

  /// Active students enrolled in a night (Hifdhu) subject.
  Future<List<Mwanafunzi>> rosterHifdhu(int somoId) =>
      _roster('/api/v1/masomo/$somoId/wanafunzi/');

  Future<List<Mwanafunzi>> _roster(String path) async {
    final raw = await _api.get(path);
    final list = raw as List<dynamic>;
    return list
        .map((row) => Mwanafunzi.fromJson(row as Map<String, dynamic>))
        .toList(growable: false);
  }

  /// Pass [darasaId] for a class roll, or [somoId] for a Hifdhu roll.
  Future<List<Hudhurio>> mahudhurio({
    int? darasaId,
    int? somoId,
    required String tarehe,
  }) async {
    final raw = await _api.get(
      '/api/v1/mahudhurio/',
      query: {
        if (somoId != null) 'somo': '$somoId' else 'darasa': '$darasaId',
        'tarehe': tarehe,
        'aina_ya_rekodi': somoId != null ? 'Hifdhu' : 'Kawaida',
      },
    );
    final list = raw as List<dynamic>;
    return list
        .map((row) => Hudhurio.fromJson(row as Map<String, dynamic>))
        .toList(growable: false);
  }

  /// Returns true if a new roll was created, false if the server already had it (409).
  Future<bool> submitMahudhurio({
    int? darasaId,
    int? somoId,
    required String tarehe,
    required List<RollDraft> rekodi,
  }) async {
    try {
      await _api.post(
        '/api/v1/mahudhurio/',
        body: {
          if (somoId != null) 'somo': somoId else 'darasa': darasaId,
          'tarehe': tarehe,
          'aina_ya_rekodi': somoId != null ? 'Hifdhu' : 'Kawaida',
          'rekodi': rekodi.map((row) => row.toJson()).toList(),
        },
      );
      return true;
    } on ApiException catch (error) {
      if (error.alreadyRecorded) {
        return false;
      }
      rethrow;
    }
  }
}
