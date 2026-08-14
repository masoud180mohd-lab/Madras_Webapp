import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madrasa_mobile/data/models/models.dart';
import 'package:madrasa_mobile/data/services/api_client.dart';
import 'package:madrasa_mobile/data/services/api_exception.dart';
import 'package:madrasa_mobile/data/services/token_store.dart';

void main() {
  group('models', () {
    test('StaffProfile parses capabilities', () {
      final profile = StaffProfile.fromJson({
        'id': 1,
        'username': 'kawaida',
        'jina': 'Mwalimu A',
        'cheo': 'Mwalimu wa Kawaida',
        'capabilities': ['attendance', 'view_students'],
      });
      expect(profile.canTakeAttendance, isTrue);
      expect(profile.canViewStudents, isTrue);
      expect(profile.canViewDirectory, isFalse);
    });

    test('RollDraft omits reason when present', () {
      final draft = RollDraft(
        mwanafunzi: const Mwanafunzi(
          id: 9,
          jinaKamili: 'Ali',
          nambaYaUsajili: 'MR-001',
          jinsia: 'ME',
        ),
        yupo: true,
        sababu: 'mgonjwa',
      );
      expect(draft.toJson()['sababu_kama_hayupo'], '');
    });
  });

  group('ApiClient', () {
    test('attaches bearer token on GET', () async {
      final tokens = MemoryTokenStore();
      await tokens.writeTokens(access: 'abc', refresh: 'r1');
      late http.BaseRequest seen;
      final client = ApiClient(
        baseUrl: 'https://example.test',
        tokens: tokens,
        httpClient: MockClient((request) async {
          seen = request;
          return http.Response(
            '[{"id":1,"jina":"Darasa la Kwanza","maelezo":null}]',
            200,
            headers: {'content-type': 'application/json'},
          );
        }),
      );
      final data = await client.get('/api/v1/madarasa/');
      expect(seen.headers['Authorization'], 'Bearer abc');
      expect(data, isA<List<dynamic>>());
    });

    test('maps 409 to alreadyRecorded', () async {
      final client = ApiClient(
        baseUrl: 'https://example.test',
        tokens: MemoryTokenStore(),
        httpClient: MockClient((request) async {
          return http.Response(
            '{"detail":"Mahudhurio ya siku hii tayari yameshajulikana."}',
            409,
            headers: {'content-type': 'application/json'},
          );
        }),
      );
      try {
        await client.post('/api/v1/mahudhurio/', body: {'darasa': 1});
        fail('expected ApiException');
      } on ApiException catch (error) {
        expect(error.alreadyRecorded, isTrue);
      }
    });
  });
}
