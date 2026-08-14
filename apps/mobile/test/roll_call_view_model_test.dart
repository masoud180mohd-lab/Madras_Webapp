import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madrasa_mobile/data/models/models.dart';
import 'package:madrasa_mobile/data/repositories/attendance_repository.dart';
import 'package:madrasa_mobile/data/services/api_client.dart';
import 'package:madrasa_mobile/data/services/token_store.dart';
import 'package:madrasa_mobile/ui/features/roll_call/view_models/roll_call_view_model.dart';

void main() {
  const darasa = Darasa(id: 2, jina: 'Darasa la Kwanza');

  ApiClient clientFor(Map<String, http.Response> routes) {
    return ApiClient(
      baseUrl: 'https://example.test',
      tokens: MemoryTokenStore(),
      httpClient: MockClient((request) async {
        final key = '${request.method} ${request.url.path}';
        final match = routes[key];
        if (match != null) {
          return match;
        }
        return http.Response('not found', 404);
      }),
    );
  }

  test('load marks already recorded when GET returns rows', () async {
    final api = clientFor({
      'GET /api/v1/madarasa/2/wanafunzi/': http.Response(
        jsonEncode([
          {
            'id': 11,
            'jina_kamili': 'Ali',
            'namba_ya_usajili': 'MR-001',
            'jinsia': 'ME',
            'picha': null,
          },
        ]),
        200,
        headers: {'content-type': 'application/json'},
      ),
      'GET /api/v1/mahudhurio/': http.Response(
        jsonEncode([
          {
            'id': 1,
            'mwanafunzi': 11,
            'tarehe': '2026-08-14',
            'yupo': false,
            'sababu_kama_hayupo': 'mgonjwa',
            'aina_ya_rekodi': 'Kawaida',
          },
        ]),
        200,
        headers: {'content-type': 'application/json'},
      ),
    });
    final vm = RollCallViewModel(
      repository: AttendanceRepository(api: api),
      darasa: darasa,
      canTakeAttendance: true,
    );
    await vm.load();
    expect(vm.alreadyRecorded, isTrue);
    expect(vm.canEdit, isFalse);
    expect(vm.rows.single.yupo, isFalse);
  });

  test('409 on save is treated as success', () async {
    final api = clientFor({
      'GET /api/v1/madarasa/2/wanafunzi/': http.Response(
        jsonEncode([
          {
            'id': 11,
            'jina_kamili': 'Ali',
            'namba_ya_usajili': 'MR-001',
            'jinsia': 'ME',
            'picha': null,
          },
        ]),
        200,
        headers: {'content-type': 'application/json'},
      ),
      'GET /api/v1/mahudhurio/': http.Response(
        '[]',
        200,
        headers: {'content-type': 'application/json'},
      ),
      'POST /api/v1/mahudhurio/': http.Response(
        '{"detail":"Mahudhurio ya siku hii tayari yameshajulikana."}',
        409,
        headers: {'content-type': 'application/json'},
      ),
    });
    final vm = RollCallViewModel(
      repository: AttendanceRepository(api: api),
      darasa: darasa,
      canTakeAttendance: true,
    );
    await vm.load();
    expect(vm.canEdit, isTrue);
    final ok = await vm.save();
    expect(ok, isTrue);
    expect(vm.alreadyRecorded, isTrue);
  });
}
