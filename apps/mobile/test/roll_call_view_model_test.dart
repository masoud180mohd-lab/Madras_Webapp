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

  test('hifdhu roll uses the night-subject roster and sends somo', () async {
    final requests = <http.Request>[];
    final api = ApiClient(
      baseUrl: 'https://example.test',
      tokens: MemoryTokenStore(),
      httpClient: MockClient((request) async {
        requests.add(request);
        final key = '${request.method} ${request.url.path}';
        if (key == 'GET /api/v1/masomo/7/wanafunzi/') {
          return http.Response(
            jsonEncode([
              {
                'id': 21,
                'jina_kamili': 'Fatma',
                'namba_ya_usajili': 'MR-021',
                'jinsia': 'KE',
                'picha': null,
              },
            ]),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (key == 'GET /api/v1/mahudhurio/') {
          return http.Response(
            '[]',
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (key == 'POST /api/v1/mahudhurio/') {
          return http.Response(
            '{"idadi":1,"aina_ya_rekodi":"Hifdhu"}',
            201,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('not found', 404);
      }),
    );
    final vm = RollCallViewModel.hifdhu(
      repository: AttendanceRepository(api: api),
      somoId: 7,
      canTakeAttendance: true,
    );
    await vm.load();
    expect(vm.isHifdhu, isTrue);
    expect(vm.rows.single.mwanafunzi.id, 21);
    final listed = requests.firstWhere(
      (r) => r.method == 'GET' && r.url.path == '/api/v1/mahudhurio/',
    );
    expect(listed.url.queryParameters['somo'], '7');
    expect(listed.url.queryParameters['aina_ya_rekodi'], 'Hifdhu');
    expect(listed.url.queryParameters.containsKey('darasa'), isFalse);

    expect(await vm.save(), isTrue);
    final posted = requests.lastWhere((r) => r.method == 'POST');
    final body = jsonDecode(posted.body) as Map<String, dynamic>;
    expect(body['somo'], 7);
    expect(body['aina_ya_rekodi'], 'Hifdhu');
    expect(body.containsKey('darasa'), isFalse);
    expect(vm.alreadyRecorded, isTrue);
  });
}
