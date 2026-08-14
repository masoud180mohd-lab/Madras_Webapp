import 'package:flutter/material.dart';

import '../../../data/models/models.dart';
import '../../../data/repositories/attendance_repository.dart';
import '../../../data/services/api_exception.dart';

class ClassesViewModel extends ChangeNotifier {
  ClassesViewModel({required AttendanceRepository repository})
    : _repository = repository;

  final AttendanceRepository _repository;

  bool _loading = false;
  String? _error;
  List<Darasa> _madarasa = const [];

  bool get loading => _loading;
  String? get error => _error;
  List<Darasa> get madarasa => _madarasa;

  Future<void> load() async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      _madarasa = await _repository.listMadarasa();
    } on ApiException catch (error) {
      _error = error.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia madarasa.';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }
}
