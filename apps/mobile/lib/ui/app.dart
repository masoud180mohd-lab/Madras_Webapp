import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/models/models.dart';
import '../data/repositories/attendance_repository.dart';
import 'core/theme.dart';
import 'features/auth/view_models/auth_view_model.dart';
import 'features/auth/views/login_view.dart';
import 'features/classes/view_models/classes_view_model.dart';
import 'features/classes/views/classes_view.dart';
import 'features/roll_call/view_models/roll_call_view_model.dart';
import 'features/roll_call/views/roll_call_view.dart';

GoRouter createRouter({
  required AuthViewModel auth,
  required AttendanceRepository attendance,
}) {
  return GoRouter(
    initialLocation: '/madarasa',
    refreshListenable: auth,
    redirect: (context, state) {
      if (!auth.ready) {
        return '/anza';
      }
      final loggingIn = state.matchedLocation == '/ingia';
      if (!auth.isLoggedIn) {
        return loggingIn ? null : '/ingia';
      }
      if (loggingIn || state.matchedLocation == '/anza') {
        return '/madarasa';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/anza',
        builder: (context, state) => const Scaffold(
          body: Center(child: CircularProgressIndicator()),
        ),
      ),
      GoRoute(
        path: '/ingia',
        builder: (context, state) => LoginView(viewModel: auth),
      ),
      GoRoute(
        path: '/madarasa',
        builder: (context, state) => ClassesView(
          auth: auth,
          viewModel: context.read<ClassesViewModel>(),
        ),
        routes: [
          GoRoute(
            path: ':id',
            builder: (context, state) {
              final extra = state.extra;
              final classes = context.read<ClassesViewModel>();
              Darasa? darasa;
              if (extra is Darasa) {
                darasa = extra;
              } else {
                final id = int.tryParse(state.pathParameters['id'] ?? '');
                if (id != null) {
                  for (final item in classes.madarasa) {
                    if (item.id == id) {
                      darasa = item;
                      break;
                    }
                  }
                }
              }
              if (darasa == null) {
                return const Scaffold(
                  body: Center(child: Text('Darasa halipatikani.')),
                );
              }
              return RollCallView(
                viewModel: RollCallViewModel(
                  repository: attendance,
                  darasa: darasa,
                  canTakeAttendance:
                      auth.profile?.canTakeAttendance ?? false,
                ),
              );
            },
          ),
        ],
      ),
    ],
  );
}

class MadrasaApp extends StatelessWidget {
  const MadrasaApp({super.key, required this.router});

  final GoRouter router;

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Al-Madrasatul Rasulillah',
      theme: MadrasaTheme.light(),
      locale: const Locale('sw'),
      routerConfig: router,
    );
  }
}
