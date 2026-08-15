import 'package:flutter/material.dart';

import '../../../../data/models/models.dart';
import '../../../../data/repositories/catalog_repository.dart';
import '../../../../data/services/api_exception.dart';

typedef CatalogLoader = Future<List<CatalogRow>> Function({String? q});

class CatalogViewModel extends ChangeNotifier {
  CatalogViewModel({required this.loader});

  final CatalogLoader loader;
  String? _query;

  bool _loading = false;
  String? _error;
  List<CatalogRow> _rows = const [];

  bool get loading => _loading;
  String? get error => _error;
  List<CatalogRow> get rows => _rows;

  Future<void> load({String? q}) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      if (q != null) {
        _query = q;
      }
      _rows = await loader(q: _query);
    } on ApiException catch (error) {
      _error = error.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia orodha.';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }
}

class DashboardViewModel extends ChangeNotifier {
  DashboardViewModel({required CatalogRepository repository})
    : _repository = repository;

  final CatalogRepository _repository;

  bool _loading = false;
  String? _error;
  DashboardSnapshot? _data;

  bool get loading => _loading;
  String? get error => _error;
  DashboardSnapshot? get data => _data;

  Future<void> load() async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      _data = await _repository.mwanzo();
    } on ApiException catch (error) {
      _error = error.message;
    } catch (_) {
      _error = 'Imeshindikana kupakia mwanzo.';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }
}
