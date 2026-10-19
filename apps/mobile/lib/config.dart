class AppConfig {
  const AppConfig({required this.apiBaseUrl});

  final String apiBaseUrl;

  static const AppConfig production = AppConfig(
    apiBaseUrl: 'https://rasulillah.me',
  );

  factory AppConfig.fromEnvironment() {
    const raw = String.fromEnvironment('API_BASE_URL');
    if (raw.isEmpty) {
      return production;
    }
    return AppConfig(apiBaseUrl: raw.replaceAll(RegExp(r'/$'), ''));
  }
}
