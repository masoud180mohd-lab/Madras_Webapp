import 'package:flutter/material.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/auth_repository.dart';
import '../../../../data/services/api_exception.dart';

class AuthViewModel extends ChangeNotifier {
  AuthViewModel({required AuthRepository repository}) : _repository = repository;

  final AuthRepository _repository;

  bool _ready = false;
  bool _busy = false;
  String? _error;
  StaffProfile? _profile;

  bool get ready => _ready;
  bool get busy => _busy;
  bool get isLoggedIn => _profile != null;
  String? get error => _error;
  StaffProfile? get profile => _profile;

  Future<void> restore() async {
    _profile = await _repository.restore();
    _ready = true;
    notifyListeners();
  }

  Future<bool> login({
    required String username,
    required String password,
  }) async {
    _busy = true;
    _error = null;
    notifyListeners();
    try {
      _profile = await _repository.login(
        username: username,
        password: password,
      );
      return true;
    } on ApiException catch (error) {
      _error = error.message;
      return false;
    } catch (_) {
      _error = 'Imeshindikana kuunganisha. Jaribu tena.';
      return false;
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    _profile = null;
    notifyListeners();
  }
}
