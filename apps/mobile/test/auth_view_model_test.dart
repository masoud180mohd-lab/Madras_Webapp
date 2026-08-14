import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madrasa_mobile/data/repositories/auth_repository.dart';
import 'package:madrasa_mobile/data/services/api_client.dart';
import 'package:madrasa_mobile/data/services/token_store.dart';
import 'package:madrasa_mobile/ui/features/auth/view_models/auth_view_model.dart';

void main() {
  test('login stores tokens and profile', () async {
    final tokens = MemoryTokenStore();
    final api = ApiClient(
      baseUrl: 'https://example.test',
      tokens: tokens,
      httpClient: MockClient((request) async {
        if (request.url.path.endsWith('/auth/token/')) {
          return http.Response(
            '{"access":"a1","refresh":"r1"}',
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response(
          '{"id":3,"username":"kawaida","jina":"Mwalimu A","cheo":"Mwalimu wa Kawaida","capabilities":["attendance"]}',
          200,
          headers: {'content-type': 'application/json'},
        );
      }),
    );
    final vm = AuthViewModel(
      repository: AuthRepository(api: api, tokens: tokens),
    );
    final ok = await vm.login(username: 'kawaida', password: 'pass12345');
    expect(ok, isTrue);
    expect(vm.isLoggedIn, isTrue);
    expect(vm.profile?.canTakeAttendance, isTrue);
    expect(await tokens.readAccess(), 'a1');
  });

  test('wrong password surfaces Swahili error', () async {
    final tokens = MemoryTokenStore();
    final api = ApiClient(
      baseUrl: 'https://example.test',
      tokens: tokens,
      httpClient: MockClient((request) async {
        return http.Response(
          '{"detail":"No active account found with the given credentials"}',
          401,
          headers: {'content-type': 'application/json'},
        );
      }),
    );
    final vm = AuthViewModel(
      repository: AuthRepository(api: api, tokens: tokens),
    );
    final ok = await vm.login(username: 'kawaida', password: 'wrong');
    expect(ok, isFalse);
    expect(vm.error, contains('No active account'));
  });
}
