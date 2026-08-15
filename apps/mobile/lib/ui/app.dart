import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../data/models/models.dart';
import '../data/repositories/attendance_repository.dart';
import '../data/repositories/catalog_repository.dart';
import 'core/copy.dart';
import 'core/theme.dart';
import 'core/theme_controller.dart';
import 'core/widgets/app_shell.dart';
import 'features/auth/view_models/auth_view_model.dart';
import 'features/auth/views/login_view.dart';
import 'features/catalog/view_models/catalog_view_model.dart';
import 'features/catalog/views/catalog_list_view.dart';
import 'features/catalog/views/entity_detail_view.dart';
import 'features/catalog/views/student_detail_view.dart';
import 'features/classes/view_models/classes_view_model.dart';
import 'features/classes/views/class_hub_view.dart';
import 'features/classes/views/classes_view.dart';
import 'features/home/views/home_view.dart';
import 'features/roll_call/view_models/roll_call_view_model.dart';
import 'features/roll_call/views/roll_call_view.dart';
import 'features/settings/views/settings_view.dart';

GoRouter createRouter({
  required AuthViewModel auth,
  required AttendanceRepository attendance,
  required CatalogRepository catalog,
}) {
  Darasa? darasaFrom(GoRouterState state, ClassesViewModel classes) {
    final extra = state.extra;
    if (extra is Darasa) {
      return extra;
    }
    final id = int.tryParse(state.pathParameters['id'] ?? '');
    if (id == null) {
      return null;
    }
    for (final item in classes.madarasa) {
      if (item.id == id) {
        return item;
      }
    }
    return Darasa(id: id, jina: 'Darasa');
  }

  return GoRouter(
    initialLocation: '/mwanzo',
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
        return '/mwanzo';
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
      ShellRoute(
        builder: (context, state, child) => AppShell(auth: auth, child: child),
        routes: [
          GoRoute(
            path: '/mwanzo',
            builder: (context, state) => HomeView(
              auth: auth,
              viewModel: DashboardViewModel(repository: catalog),
            ),
          ),
          GoRoute(
            path: '/walimu',
            builder: (context, state) => CatalogListView(
              viewModel: CatalogViewModel(loader: ({q}) => catalog.walimu()),
            ),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) {
                  final id = int.tryParse(state.pathParameters['id'] ?? '');
                  return EntityDetailView(
                    heading: MadrasaCopy.teachers,
                    loader: () async {
                      final rows = await catalog.walimu();
                      return rows.firstWhere((row) => row.id == id);
                    },
                  );
                },
              ),
            ],
          ),
          GoRoute(
            path: '/wanafunzi',
            builder: (context, state) {
              final darasa = state.uri.queryParameters['darasa'];
              return CatalogListView(
                searchable: darasa == null,
                viewModel: CatalogViewModel(
                  loader: ({q}) => catalog.wanafunzi(q: q, darasa: darasa),
                ),
              );
            },
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) {
                  final id = int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
                  return StudentDetailView(
                    studentId: id,
                    repository: catalog,
                  );
                },
              ),
            ],
          ),
          GoRoute(
            path: '/masomo',
            builder: (context, state) => CatalogListView(
              viewModel: CatalogViewModel(loader: ({q}) => catalog.masomo()),
            ),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) {
                  final id = int.tryParse(state.pathParameters['id'] ?? '');
                  return EntityDetailView(
                    heading: MadrasaCopy.subjects,
                    loader: () async {
                      final rows = await catalog.masomo();
                      return rows.firstWhere((row) => row.id == id);
                    },
                  );
                },
              ),
            ],
          ),
          GoRoute(
            path: '/madarasa',
            builder: (context, state) => ClassesView(
              viewModel: context.read<ClassesViewModel>(),
            ),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) {
                  final darasa = darasaFrom(
                    state,
                    context.read<ClassesViewModel>(),
                  );
                  if (darasa == null) {
                    return const Center(child: Text('Darasa halipatikani.'));
                  }
                  return ClassHubView(
                    darasa: darasa,
                    canTakeAttendance:
                        auth.profile?.canTakeAttendance ?? false,
                    canViewStudents: auth.profile?.canViewStudents ?? false,
                  );
                },
                routes: [
                  GoRoute(
                    path: 'mahudhurio',
                    builder: (context, state) {
                      final darasa = darasaFrom(
                        state,
                        context.read<ClassesViewModel>(),
                      );
                      if (darasa == null) {
                        return const Center(child: Text('Darasa halipatikani.'));
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
          ),
          GoRoute(
            path: '/watoro',
            builder: (context, state) => CatalogListView(
              viewModel: CatalogViewModel(loader: ({q}) => catalog.watoro()),
            ),
          ),
          GoRoute(
            path: '/malipo',
            builder: (context, state) => CatalogListView(
              viewModel: CatalogViewModel(loader: ({q}) => catalog.malipo()),
            ),
          ),
          GoRoute(
            path: '/aina-malipo',
            builder: (context, state) => CatalogListView(
              viewModel: CatalogViewModel(loader: ({q}) => catalog.ainaMalipo()),
            ),
          ),
          GoRoute(
            path: '/mwaka',
            builder: (context, state) => CatalogListView(
              viewModel: CatalogViewModel(loader: ({q}) => catalog.mwaka()),
            ),
          ),
          GoRoute(
            path: '/hamisha',
            builder: (context, state) => CatalogListView(
              hint: MadrasaCopy.promoteHint,
              viewModel: CatalogViewModel(loader: ({q}) => catalog.hamisha()),
            ),
          ),
          GoRoute(
            path: '/mawasiliano',
            builder: (context, state) => CatalogListView(
              searchable: true,
              viewModel: CatalogViewModel(
                loader: ({q}) => catalog.mawasiliano(q: q),
              ),
            ),
          ),
          GoRoute(
            path: '/ukaguzi',
            builder: (context, state) => CatalogListView(
              viewModel: CatalogViewModel(loader: ({q}) => catalog.ukaguzi()),
            ),
          ),
          GoRoute(
            path: '/mipangilio',
            builder: (context, state) => SettingsView(auth: auth),
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
    final theme = context.watch<ThemeController>();
    return MaterialApp.router(
      title: 'Al-Madrasatul Rasulillah',
      theme: MadrasaTheme.light(),
      darkTheme: MadrasaTheme.dark(),
      themeMode: theme.mode,
      locale: const Locale('sw'),
      routerConfig: router,
    );
  }
}
