import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madrasa_mobile/data/repositories/catalog_repository.dart';
import 'package:madrasa_mobile/data/services/api_client.dart';
import 'package:madrasa_mobile/data/services/token_store.dart';
import 'package:madrasa_mobile/ui/features/catalog/views/hifdhu_students_view.dart';
import 'package:madrasa_mobile/ui/features/catalog/views/subject_detail_view.dart';
import 'package:provider/provider.dart';

void main() {
  testWidgets('subject detail displays hifdhu layout without materials/exams', (tester) async {
    tester.view.physicalSize = const Size(1200, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    final api = ApiClient(
      baseUrl: 'https://example.test',
      tokens: MemoryTokenStore(),
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/masomo/10/') {
          return http.Response(
            jsonEncode({
              'id': 10,
              'jina': 'Hifdhu Usiku',
              'darasa': null,
              'darasa_jina': null,
              'mwalimu': 'Sheikh Ali',
              'ni_la_hifdhu': true,
              'nyenzo': <dynamic>[],
              'mitihani': <dynamic>[],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path == '/api/v1/masomo/10/wanafunzi/') {
          return http.Response(
            jsonEncode([
              {
                'id': 1,
                'jina_kamili': 'Fatma Zahra',
                'namba_ya_usajili': 'MR-001',
              },
            ]),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('{"detail":"Not found"}', 404);
      }),
    );

    await tester.pumpWidget(
      Provider<ApiClient>.value(
        value: api,
        child: MaterialApp(
          home: Scaffold(
            body: SubjectDetailView(
              somoId: 10,
              repository: CatalogRepository(api: api),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // Verify Hifdhu hub components
    expect(find.text('Hifdhu Usiku'), findsOneWidget);
    expect(find.text('Mahudhurio'), findsOneWidget);
    expect(find.text('Rekodi sabaq na murajaa'), findsOneWidget);
    expect(find.text('Mwalimu: Sheikh Ali'), findsOneWidget);

    // Verify classroom materials & exams are omitted
    expect(find.text('Nyenzo za Somo'), findsNothing);
    expect(find.text('Mitihani ya Somo'), findsNothing);
  });

  testWidgets('hifdhu students roster displays students with sabaq and ripoti buttons', (tester) async {
    tester.view.physicalSize = const Size(1200, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    final api = ApiClient(
      baseUrl: 'https://example.test',
      tokens: MemoryTokenStore(),
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/masomo/10/') {
          return http.Response(
            jsonEncode({
              'id': 10,
              'jina': 'Hifdhu Usiku',
              'darasa': null,
              'darasa_jina': null,
              'mwalimu': 'Sheikh Ali',
              'ni_la_hifdhu': true,
              'nyenzo': <dynamic>[],
              'mitihani': <dynamic>[],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path == '/api/v1/masomo/10/wanafunzi/') {
          return http.Response(
            jsonEncode([
              {
                'id': 1,
                'jina_kamili': 'Fatma Zahra',
                'namba_ya_usajili': 'MR-001',
                'jinsia': 'KE',
              },
            ]),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('{"detail":"Not found"}', 404);
      }),
    );

    await tester.pumpWidget(
      Provider<ApiClient>.value(
        value: api,
        child: MaterialApp(
          home: Scaffold(
            body: HifdhuStudentsView(
              somoId: 10,
              repository: CatalogRepository(api: api),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Wanafunzi: Hifdhu Usiku'), findsOneWidget);
    expect(find.text('Fatma Zahra'), findsOneWidget);
    expect(find.text('Ripoti'), findsOneWidget);
    expect(find.text('Sabaq'), findsOneWidget);
  });
}
