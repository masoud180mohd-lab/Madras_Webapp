class AppConfig {
  const AppConfig({required this.apiBaseUrl});

  final String apiBaseUrl;

  static const AppConfig production = AppConfig(
    // TODO: Replace with the exact Render service URL after first deploy if Render assigns a different hostname.
    apiBaseUrl: 'https://madrasa-webapp.onrender.com',
  );

  factory AppConfig.fromEnvironment() {
    const raw = String.fromEnvironment('API_BASE_URL');
    if (raw.isEmpty) {
      return production;
    }
    return AppConfig(apiBaseUrl: raw.replaceAll(RegExp(r'/$'), ''));
  }
}
