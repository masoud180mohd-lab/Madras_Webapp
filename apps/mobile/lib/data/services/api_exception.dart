class ApiException implements Exception {
  const ApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  bool get isUnauthorized => statusCode == 401;
  bool get isForbidden => statusCode == 403;
  bool get alreadyRecorded => statusCode == 409;

  @override
  String toString() => 'ApiException($statusCode): $message';
}
