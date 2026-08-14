import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madrasa_mobile/data/repositories/auth_repository.dart';
import 'package:madrasa_mobile/data/services/api_client.dart';
import 'package:madrasa_mobile/data/services/token_store.dart';
import 'package:madrasa_mobile/ui/core/copy.dart';
import 'package:madrasa_mobile/ui/features/auth/view_models/auth_view_model.dart';
import 'package:madrasa_mobile/ui/features/auth/views/login_view.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  testWidgets('login screen shows Karibu Ndani and validates empty username', (
    tester,
  ) async {
    final vm = AuthViewModel(
      repository: AuthRepository(
        api: ApiClient(
          baseUrl: 'https://example.test',
          tokens: MemoryTokenStore(),
          httpClient: MockClient((request) async => http.Response('{}', 500)),
        ),
        tokens: MemoryTokenStore(),
      ),
    );
    await tester.pumpWidget(
      MaterialApp(home: LoginView(viewModel: vm)),
    );
    expect(find.text(MadrasaCopy.welcome), findsOneWidget);
    expect(find.text(MadrasaCopy.brand), findsOneWidget);
    await tester.ensureVisible(find.byKey(const Key('login_submit')));
    await tester.pump();
    await tester.tap(find.byKey(const Key('login_submit')));
    await tester.pump();
    expect(find.text(MadrasaCopy.needUsername), findsOneWidget);
  });
}
