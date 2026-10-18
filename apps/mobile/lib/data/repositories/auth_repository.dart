import 'dart:developer' as developer;

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
    developer.log('Login attempt for user: $username', name: 'AuthRepository.login');
    try {
      final raw = await _api.post(
        '/api/v1/auth/token/',
        body: {'username': username.trim(), 'password': password},
        auth: false,
      );
      developer.log('Login successful, parsing response', name: 'AuthRepository.login');
      final tokens = TokenPair.fromJson(raw as Map<String, dynamic>);
      await _tokens.writeTokens(access: tokens.access, refresh: tokens.refresh);
      developer.log('Tokens saved, fetching profile', name: 'AuthRepository.login');
      return fetchMe();
    } catch (e, stack) {
      developer.log('Login error: $e\nStack: $stack', name: 'AuthRepository.login', level: 1000);
      rethrow;
    }
  }

  Future<StaffProfile?> restore() async {
    developer.log('Attempting to restore session', name: 'AuthRepository.restore');
    final access = await _tokens.readAccess();
    if (access == null || access.isEmpty) {
      developer.log('No saved access token found', name: 'AuthRepository.restore');
      return null;
    }
    try {
      developer.log('Access token found, fetching profile', name: 'AuthRepository.restore');
      return await fetchMe();
    } catch (e) {
      developer.log('Session restore failed: $e', name: 'AuthRepository.restore', level: 1000);
      await _tokens.clear();
      return null;
    }
  }

  Future<StaffProfile> fetchMe() async {
    developer.log('Fetching user profile', name: 'AuthRepository.fetchMe');
    try {
      final raw = await _api.get('/api/v1/me/');
      developer.log('Profile fetched successfully', name: 'AuthRepository.fetchMe');
      return StaffProfile.fromJson(raw as Map<String, dynamic>);
    } catch (e, stack) {
      developer.log('Profile fetch error: $e\nStack: $stack', name: 'AuthRepository.fetchMe', level: 1000);
      rethrow;
    }
  }

  Future<void> logout() => _tokens.clear();
}
