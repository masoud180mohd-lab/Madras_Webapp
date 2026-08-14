import '../models/models.dart';
import '../services/api_client.dart';
import '../services/token_store.dart';

class AuthRepository {
  AuthRepository({required ApiClient api, required TokenStore tokens})
    : _api = api,
      _tokens = tokens;

  final ApiClient _api;
  final TokenStore _tokens;

  Future<StaffProfile> login({
    required String username,
    required String password,
  }) async {
    final raw = await _api.post(
      '/api/v1/auth/token/',
      body: {'username': username.trim(), 'password': password},
      auth: false,
    );
    final tokens = TokenPair.fromJson(raw as Map<String, dynamic>);
    await _tokens.writeTokens(access: tokens.access, refresh: tokens.refresh);
    return fetchMe();
  }

  Future<StaffProfile?> restore() async {
    final access = await _tokens.readAccess();
    if (access == null || access.isEmpty) {
      return null;
    }
    try {
      return await fetchMe();
    } catch (_) {
      await _tokens.clear();
      return null;
    }
  }

  Future<StaffProfile> fetchMe() async {
    final raw = await _api.get('/api/v1/me/');
    return StaffProfile.fromJson(raw as Map<String, dynamic>);
  }

  Future<void> logout() => _tokens.clear();
}
