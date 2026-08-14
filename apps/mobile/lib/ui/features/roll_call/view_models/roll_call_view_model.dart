import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../data/models/models.dart';
import '../../../data/repositories/attendance_repository.dart';
import '../../../data/services/api_exception.dart';

class RollCallViewModel extends ChangeNotifier {
  RollCallViewModel({
    required AttendanceRepository repository,
    required this.darasa,
    required this.canTakeAttendance,
  }) : _repository = repository;

  final AttendanceRepository _repository;
  final Darasa darasa;
  final bool canTakeAttendance;

  bool _loading = false;
  bool _saving = false;
  bool _alreadyRecorded = false;
  String? _error;
  String? _notice;
  List<RollDraft> _rows = const [];

  bool get loading => _loading;
  bool get saving => _saving;
  bool get alreadyRecorded => _alreadyRecorded;
  bool get canEdit => canTakeAttendance && !_alreadyRecorded;
  String? get error => _error;
  String? get notice => _notice;
  List<RollDraft> get rows => _rows;
  String get tarehe => DateFormat('yyyy-MM-dd').format(DateTime.now());
  int get presentCount => _rows.where((row) => row.yupo).length;

  Future<void> load() async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      final wanafunzi = await _repository.roster(darasa.id);
      final existing = canTakeAttendance
          ? await _repository.mahudhurio(darasaId: darasa.id, tarehe: tarehe)
          : const <Hudhurio>[];
      final byId = {for (final row in existing) row.mwanafunziId: row};
      _alreadyRecorded = existing.isNotEmpty;
      _rows = [
        for (final student in wanafunzi)
          RollDraft(
            mwanafunzi: student,
            yupo: byId[student.id]?.yupo ?? true,
            sababu: byId[student.id]?.sababuKamaHayupo ?? '',
          ),
      ];
    } on ApiException catch (error) {
      _error = error.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia orodha.';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  void setYupo(int mwanafunziId, bool yupo) {
    if (!canEdit) {
      return;
    }
    final row = _rows.firstWhere((item) => item.mwanafunzi.id == mwanafunziId);
    row.yupo = yupo;
    if (yupo) {
      row.sababu = '';
    }
    notifyListeners();
  }

  void setSababu(int mwanafunziId, String sababu) {
    if (!canEdit) {
      return;
    }
    final row = _rows.firstWhere((item) => item.mwanafunzi.id == mwanafunziId);
    row.sababu = sababu;
    notifyListeners();
  }

  Future<bool> save() async {
    if (!canEdit) {
      return false;
    }
    _saving = true;
    _error = null;
    _notice = null;
    notifyListeners();
    try {
      final created = await _repository.submitMahudhurio(
        darasaId: darasa.id,
        tarehe: tarehe,
        rekodi: _rows,
      );
      _alreadyRecorded = true;
      _notice = created
          ? 'Mahudhurio yamehifadhiwa.'
          : 'Mahudhurio ya leo tayari yameshajulikana.';
      return true;
    } on ApiException catch (error) {
      _error = error.message;
      return false;
    } catch (_) {
      _error = 'Imeshindikana kuhifadhi mahudhurio.';
      return false;
    } finally {
      _saving = false;
      notifyListeners();
    }
  }
}
