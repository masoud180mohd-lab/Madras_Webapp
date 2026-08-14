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

  Future<List<Mwanafunzi>> roster(int darasaId) async {
    final raw = await _api.get('/api/v1/madarasa/$darasaId/wanafunzi/');
    final list = raw as List<dynamic>;
    return list
        .map((row) => Mwanafunzi.fromJson(row as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<List<Hudhurio>> mahudhurio({
    required int darasaId,
    required String tarehe,
  }) async {
    final raw = await _api.get(
      '/api/v1/mahudhurio/',
      query: {
        'darasa': '$darasaId',
        'tarehe': tarehe,
        'aina_ya_rekodi': 'Kawaida',
      },
    );
    final list = raw as List<dynamic>;
    return list
        .map((row) => Hudhurio.fromJson(row as Map<String, dynamic>))
        .toList(growable: false);
  }

  /// Returns true if a new roll was created, false if the server already had it (409).
  Future<bool> submitMahudhurio({
    required int darasaId,
    required String tarehe,
    required List<RollDraft> rekodi,
  }) async {
    try {
      await _api.post(
        '/api/v1/mahudhurio/',
        body: {
          'darasa': darasaId,
          'tarehe': tarehe,
          'aina_ya_rekodi': 'Kawaida',
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
