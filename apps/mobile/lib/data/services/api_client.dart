import 'dart:convert';

import 'package:http/http.dart' as http;

import 'api_exception.dart';
import 'token_store.dart';

class ApiClient {
  ApiClient({
    required this.baseUrl,
    required TokenStore tokens,
    http.Client? httpClient,
  }) : _tokens = tokens,
       _http = httpClient ?? http.Client();

  final String baseUrl;
  final TokenStore _tokens;
  final http.Client _http;

  Uri _uri(String path, [Map<String, String>? query]) {
    final root = baseUrl.replaceAll(RegExp(r'/$'), '');
    return Uri.parse('$root$path').replace(queryParameters: query);
  }

  Future<Map<String, String>> _headers({bool jsonBody = false}) async {
    final headers = <String, String>{
      'Accept': 'application/json',
    };
    if (jsonBody) {
      headers['Content-Type'] = 'application/json; charset=UTF-8';
    }
    final access = await _tokens.readAccess();
    if (access != null && access.isNotEmpty) {
      headers['Authorization'] = 'Bearer $access';
    }
    return headers;
  }

  Future<dynamic> get(String path, {Map<String, String>? query}) {
    return _send(() async {
      return _http.get(_uri(path, query), headers: await _headers());
    });
  }

  Future<dynamic> post(String path, {Object? body, bool auth = true}) {
    return _send(() async {
      final headers = await _headers(jsonBody: true);
      if (!auth) {
        headers.remove('Authorization');
      }
      return _http.post(
        _uri(path),
        headers: headers,
        body: body == null ? null : jsonEncode(body),
      );
    }, retryOn401: auth);
  }

  Future<http.Response> getBytes(String url) async {
    final headers = await _headers();
    final response = await _http.get(Uri.parse(url), headers: headers);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(response.statusCode, 'Imeshindikana kupakua picha.');
    }
    return response;
  }

  Future<dynamic> _send(
    Future<http.Response> Function() request, {
    bool retryOn401 = true,
  }) async {
    var response = await request();
    if (response.statusCode == 401 && retryOn401) {
      final refreshed = await _refresh();
      if (refreshed) {
        response = await request();
      }
    }
    return _decode(response);
  }

  Future<bool> _refresh() async {
    final refresh = await _tokens.readRefresh();
    if (refresh == null || refresh.isEmpty) {
      return false;
    }
    final response = await _http.post(
      _uri('/api/v1/auth/refresh/'),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode({'refresh': refresh}),
    );
    if (response.statusCode != 200) {
      await _tokens.clear();
      return false;
    }
    final data = jsonDecode(response.body);
    if (data is! Map<String, dynamic>) {
      return false;
    }
    final access = data['access'] as String?;
    final newRefresh = data['refresh'] as String? ?? refresh;
    if (access == null) {
      return false;
    }
    await _tokens.writeTokens(access: access, refresh: newRefresh);
    return true;
  }

  dynamic _decode(http.Response response) {
    final code = response.statusCode;
    dynamic decoded;
    if (response.body.isNotEmpty) {
      decoded = jsonDecode(response.body);
    }
    if (code >= 200 && code < 300) {
      return decoded;
    }
    throw ApiException(code, _messageFrom(decoded, code));
  }

  String _messageFrom(dynamic decoded, int code) {
    if (decoded is Map<String, dynamic>) {
      final detail = decoded['detail'];
      if (detail is String && detail.isNotEmpty) {
        return detail;
      }
      final rekodi = decoded['rekodi'];
      if (rekodi is List && rekodi.isNotEmpty) {
        return rekodi.first.toString();
      }
    }
    if (code == 401) {
      return 'Jina la mtumiaji au nenosiri si sahihi.';
    }
    if (code == 403) {
      return 'Huna ruhusa ya kitendo hiki.';
    }
    if (code == 409) {
      return 'Mahudhurio ya siku hii tayari yameshajulikana.';
    }
    return 'Hitilafu ya mtandao ($code).';
  }
}
