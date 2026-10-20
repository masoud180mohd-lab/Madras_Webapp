import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madrasa_mobile/data/repositories/catalog_repository.dart';
import 'package:madrasa_mobile/data/services/api_client.dart';
import 'package:madrasa_mobile/data/services/token_store.dart';
import 'package:madrasa_mobile/ui/features/catalog/views/student_detail_view.dart';
import 'package:provider/provider.dart';

void main() {
  final requests = <String>[];

  Map<String, dynamic> student() => {
    'id': 5,
    'jina_kamili': 'Amina Tab',
    'namba_ya_usajili': 'MR-005',
    'jinsia': 'KE',
    'darasa': 'Darasa la Pili',
    'picha': null,
    'tarehe_ya_kuzaliwa': null,
    'mahala_anapoishi': null,
    'programu_usiku': 'Qur\'an',
    'juzuu_aliyohifadhi': 3,
    'tarehe_ya_kujiunga': null,
    'jina_la_mzazi': null,
    'namba_ya_simu_mzazi': null,
    'uhusiano_wa_mlezi': null,
    'jina_la_mzazi_pili': null,
    'namba_ya_simu_mzazi_pili': null,
    'uhusiano_wa_mlezi_pili': null,
  };

  ApiClient client() {
    return ApiClient(
      baseUrl: 'https://example.test',
      tokens: MemoryTokenStore(),
      httpClient: MockClient((request) async {
        final tab = request.url.queryParameters['tab'];
        requests.add('${request.url.path}?tab=$tab');
        final body = switch (tab) {
          'muhtasari' => {
            'tab': 'muhtasari',
            'mwanafunzi': student(),
            'muhtasari': {
              'jumla_malipo': '3000',
              'idadi_malipo': 1,
              'mahudhurio_mchana': 4,
              'mahudhurio_hifdhu': 2,
              'idadi_sabaq': 7,
              'idadi_maendeleo': 3,
            },
          },
          'malipo' => {
            'tab': 'malipo',
            'jumla_malipo': '3000',
            'malipo': [
              {
                'id': 1,
                'tarehe': '2026-10-01',
                'aina': 'Ada ya mwezi',
                'kiasi': '3000',
                'njia': 'Cash',
                'alirekodi': 'Mwalimu A',
              },
            ],
          },
          'mahudhurio' => {
            'tab': 'mahudhurio',
            'kawaida': [
              {'tarehe': '2026-10-01', 'yupo': true, 'hali': 'Yupo'},
            ],
            'hifdhu': [
              {'tarehe': '2026-10-02', 'yupo': false, 'hali': 'Hayupo'},
            ],
          },
          'rekodi' => {
            'tab': 'rekodi',
            'sabaq_darasa': [
              {
                'tarehe': '2026-10-01',
                'sura': 'Al-Fatiha',
                'hali': 'Kajua',
                'somo': null,
              },
            ],
            'sabaq_usiku': <Map<String, dynamic>>[],
            'maendeleo_mchana': [
              {
                'tarehe': '2026-10-03',
                'somo': 'Fiqhi',
                'mada': 'Mlango wa udhu',
                'hali': '✅ Ameelewa',
              },
            ],
          },
          _ => null,
        };
        return http.Response(
          jsonEncode(body ?? {'detail': 'Tab si sahihi.'}),
          body == null ? 400 : 200,
          headers: {'content-type': 'application/json'},
        );
      }),
    );
  }

  testWidgets('student details show the four profile tabs', (tester) async {
    tester.view.physicalSize = const Size(1200, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    final api = client();
    await tester.pumpWidget(
      Provider<ApiClient>.value(
        value: api,
        child: MaterialApp(
          home: Scaffold(
            body: StudentDetailView(
              studentId: 5,
              repository: CatalogRepository(api: api),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Amina Tab'), findsOneWidget);
    expect(find.text('Muhtasari'), findsOneWidget);
    expect(find.text('Malipo'), findsOneWidget);
    expect(find.text('Mahudhurio'), findsOneWidget);
    expect(find.text('Rekodi'), findsOneWidget);
    expect(find.text('Malipo Yote'), findsOneWidget);
    expect(find.text('Tsh 3,000'), findsOneWidget);

    await tester.tap(find.text('Malipo'));
    await tester.pumpAndSettle();
    expect(find.text('Historia ya Malipo'), findsOneWidget);
    expect(find.text('3,000/='), findsOneWidget);

    await tester.tap(find.text('Mahudhurio'));
    await tester.pumpAndSettle();
    expect(find.text('Mahudhurio ya Madrasa'), findsOneWidget);
    expect(find.text('Mahudhurio ya Hifdhu'), findsOneWidget);

    await tester.tap(find.text('Rekodi'));
    await tester.pumpAndSettle();
    expect(find.text('Sabaq ya Darasa'), findsOneWidget);
    expect(find.text('Maendeleo ya mchana'), findsWidgets);
    expect(find.textContaining('Fiqhi'), findsWidgets);

    // Each tab is fetched once and kept while switching back.
    await tester.tap(find.text('Malipo'));
    await tester.pumpAndSettle();
    expect(requests.where((path) => path.contains('tab=malipo')), hasLength(1));
  });
}
