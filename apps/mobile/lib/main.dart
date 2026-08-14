import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'config.dart';
import 'data/repositories/attendance_repository.dart';
import 'data/repositories/auth_repository.dart';
import 'data/services/api_client.dart';
import 'data/services/secure_token_store.dart';
import 'ui/app.dart';
import 'ui/features/auth/view_models/auth_view_model.dart';
import 'ui/features/classes/view_models/classes_view_model.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final config = AppConfig.fromEnvironment();
  final tokens = SecureTokenStore();
  final api = ApiClient(baseUrl: config.apiBaseUrl, tokens: tokens);
  final authRepository = AuthRepository(api: api, tokens: tokens);
  final attendanceRepository = AttendanceRepository(api: api);
  final auth = AuthViewModel(repository: authRepository);
  final classes = ClassesViewModel(repository: attendanceRepository);
  final router = createRouter(auth: auth, attendance: attendanceRepository);

  await auth.restore();

  runApp(
    MultiProvider(
      providers: [
        Provider<ApiClient>.value(value: api),
        ChangeNotifierProvider<AuthViewModel>.value(value: auth),
        ChangeNotifierProvider<ClassesViewModel>.value(value: classes),
      ],
      child: MadrasaApp(router: router),
    ),
  );
}
