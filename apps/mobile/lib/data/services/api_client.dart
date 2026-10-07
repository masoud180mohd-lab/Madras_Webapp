import 'dart:convert';
import 'dart:developer' as developer;

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
      final uri = _uri(path, query);
      developer.log('GET $uri', name: 'ApiClient.get');
      return _http.get(uri, headers: await _headers());
    });
  }

  Future<dynamic> post(String path, {Object? body, bool auth = true}) {
    return _send(() async {
      final uri = _uri(path);
      final headers = await _headers(jsonBody: true);
      if (!auth) {
        headers.remove('Authorization');
      }
      developer.log('POST $uri | Auth: $auth | Body: ${jsonEncode(body)}', name: 'ApiClient.post');
      return _http.post(
        uri,
        headers: headers,
        body: body == null ? null : jsonEncode(body),
      );
    }, retryOn401: auth);
  }

  Future<dynamic> put(String path, {Object? body}) {
    return _send(() async {
      return _http.put(
        _uri(path),
        headers: await _headers(jsonBody: true),
        body: body == null ? null : jsonEncode(body),
      );
    });
  }

  Future<dynamic> postMultipart(
    String path, {
    required Map<String, String> fields,
    required String fileField,
    required List<int> bytes,
    required String filename,
  }) {
    return _send(() async {
      final request = http.MultipartRequest('POST', _uri(path));
      final headers = await _headers();
      request.headers.addAll(headers);
      request.fields.addAll(fields);
      request.files.add(
        http.MultipartFile.fromBytes(fileField, bytes, filename: filename),
      );
      final streamed = await _http.send(request);
      return await http.Response.fromStream(streamed);
    });
  }

  Future<http.Response> getBytes(String url) async {
    final headers = await _headers();
    final response = await _http.get(Uri.parse(url), headers: headers);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(response.statusCode, 'Imeshindikana kupakua faili.');
    }
    return response;
  }

  Future<dynamic> _send(
    Future<http.Response> Function() request, {
    bool retryOn401 = true,
  }) async {
    try {
      var response = await request();
      developer.log('Response: ${response.statusCode} | Body length: ${response.body.length}', name: 'ApiClient._send');
      if (response.statusCode == 401 && retryOn401) {
        developer.log('Got 401, attempting token refresh...', name: 'ApiClient._send');
        final refreshed = await _refresh();
        if (refreshed) {
          developer.log('Token refreshed successfully, retrying request', name: 'ApiClient._send');
          response = await request();
        }
      }
      return _decode(response);
    } catch (e, stack) {
      developer.log('Request error: $e\nStack: $stack', name: 'ApiClient._send', level: 1000);
      rethrow;
    }
  }

  Future<bool> _refresh() async {
    developer.log('Attempting to refresh token...', name: 'ApiClient._refresh');
    final refresh = await _tokens.readRefresh();
    if (refresh == null || refresh.isEmpty) {
      developer.log('No refresh token available', name: 'ApiClient._refresh', level: 1000);
      return false;
    }
    try {
      final response = await _http.post(
        _uri('/api/v1/auth/refresh/'),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json; charset=UTF-8',
        },
        body: jsonEncode({'refresh': refresh}),
      );
      developer.log('Token refresh response: ${response.statusCode}', name: 'ApiClient._refresh');
      if (response.statusCode != 200) {
        developer.log('Token refresh failed: ${response.body}', name: 'ApiClient._refresh', level: 1000);
        await _tokens.clear();
        return false;
      }
      final data = jsonDecode(response.body);
      if (data is! Map<String, dynamic>) {
        developer.log('Invalid token response format', name: 'ApiClient._refresh', level: 1000);
        return false;
      }
      final access = data['access'] as String?;
      final newRefresh = data['refresh'] as String? ?? refresh;
      if (access == null) {
        developer.log('No access token in refresh response', name: 'ApiClient._refresh', level: 1000);
        return false;
      }
      await _tokens.writeTokens(access: access, refresh: newRefresh);
      developer.log('Token refreshed successfully', name: 'ApiClient._refresh');
      return true;
    } catch (e, stack) {
      developer.log('Token refresh error: $e\nStack: $stack', name: 'ApiClient._refresh', level: 1000);
      return false;
    }
  }

  dynamic _decode(http.Response response) {
    final code = response.statusCode;
    dynamic decoded;
    if (response.body.isNotEmpty) {
      try {
        decoded = jsonDecode(response.body);
        developer.log('Decoded response successfully', name: 'ApiClient._decode');
      } catch (e) {
        developer.log('JSON decode error: $e | Body: ${response.body.substring(0, 200)}', name: 'ApiClient._decode', level: 1000);
        return null;
      }
    }
    if (code >= 200 && code < 300) {
      return decoded;
    }
    final errorMsg = _messageFrom(decoded, code);
    developer.log('Error response: $code | Message: $errorMsg', name: 'ApiClient._decode', level: 1000);
    throw ApiException(code, errorMsg);
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
    if (code == 0 || code == -1) {
      return 'Hakuna muunganisho wa mtandao. Tafadhali kuangalia Wi-Fi au mobile data.';
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
    if (code >= 500) {
      return 'Hitilafu ya seva ($code). Tafadhali jaribu baadaye.';
    }
    return 'Hitilafu ya mtandao ($code). Tafadhali kuangalia muunganisho wako.';
  }
}
