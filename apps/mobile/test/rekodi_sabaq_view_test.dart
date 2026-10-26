import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madrasa_mobile/data/models/models.dart';
import 'package:madrasa_mobile/data/repositories/catalog_repository.dart';
import 'package:madrasa_mobile/data/services/api_client.dart';
import 'package:madrasa_mobile/data/services/token_store.dart';
import 'package:madrasa_mobile/ui/features/catalog/views/rekodi_sabaq_view.dart';
import 'package:provider/provider.dart';

void main() {
  testWidgets('RekodiSabaqView renders fields and submits form successfully', (tester) async {
    tester.view.physicalSize = const Size(1200, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    Map<String, dynamic>? recordedBody;

    final api = ApiClient(
      baseUrl: 'https://example.test',
      tokens: MemoryTokenStore(),
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/sabaq/' && request.method == 'POST') {
          recordedBody = jsonDecode(request.body) as Map<String, dynamic>;
          return http.Response(
            jsonEncode({'id': 99, 'status': 'success'}),
            201,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('{"detail":"Not found"}', 404);
      }),
    );

    final student = const Mwanafunzi(
      id: 5,
      jinaKamili: 'Ali Hassan',
      nambaYaUsajili: 'MAD-005',
      jinsia: 'ME',
    );

    await tester.pumpWidget(
      Provider<ApiClient>.value(
        value: api,
        child: MaterialApp(
          home: RekodiSabaqView(
            mwanafunziId: 5,
            mwanafunzi: student,
            repository: CatalogRepository(api: api),
            aina: 'Usiku',
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Rekodi Sabaq & Murajaa'), findsOneWidget);
    expect(find.text('Ali Hassan'), findsOneWidget);
    expect(find.text('MAD-005 · Kipindi cha Usiku'), findsOneWidget);
    expect(find.text('Sura ya Kuhifadhi (Sabaq Mpya)'), findsOneWidget);

    // Enter Sura and Aya
    await tester.enterText(find.widgetWithText(TextFormField, 'Jina la Sura au Juzuu'), 'Al-Mulk');
    await tester.enterText(find.widgetWithText(TextFormField, 'Aya Kuanzia'), '1');
    await tester.enterText(find.widgetWithText(TextFormField, 'Aya Kuishia'), '15');
    await tester.enterText(find.widgetWithText(TextFormField, 'Maoni / Maelezo ya Murajaa (hiari)'), 'Vizuri sana');

    // Tap submit
    await tester.tap(find.text('Hifadhi Sabaq'));
    await tester.pumpAndSettle();

    expect(recordedBody, isNotNull);
    expect(recordedBody!['mwanafunzi'], 5);
    expect(recordedBody!['aina_ya_rekodi'], 'Usiku');
    expect(recordedBody!['sabaq_sura'], 'Al-Mulk');
    expect(recordedBody!['sabaq_aya_kuanzia'], 1);
    expect(recordedBody!['sabaq_aya_kuishia'], 15);
    expect(recordedBody!['sabaq_hali'], 'Kajua');
    expect(recordedBody!['maoni_ya_mwalimu'], 'Vizuri sana');
  });
}
