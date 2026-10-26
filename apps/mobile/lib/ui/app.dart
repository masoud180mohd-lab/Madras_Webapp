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
import 'features/catalog/views/catalog_actions.dart';
import 'features/catalog/views/catalog_list_view.dart';
import 'features/catalog/views/entity_detail_view.dart';
import 'features/catalog/views/exam_results_view.dart';
import 'features/catalog/views/hifdhu_students_view.dart';
import 'features/catalog/views/rekodi_sabaq_view.dart';
import 'features/catalog/views/student_detail_view.dart';
import 'features/catalog/views/subject_detail_view.dart';
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
              topBar: (auth.profile?.canManageStudents ?? false)
                  ? (ctx, reload) => CatalogActions.walimuTopBar(
                        context: ctx,
                        repo: catalog,
                        reload: reload,
                      )
                  : null,
            ),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) {
                  final id =
                      int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
                  return EntityDetailView(
                    heading: MadrasaCopy.teachers,
                    loader: () async {
                      final rows = await catalog.walimu();
                      return rows.firstWhere((row) => row.id == id);
                    },
                    actionBuilder: (auth.profile?.canManageStudents ?? false)
                        ? (ctx, row, reload) => Align(
                              alignment: Alignment.centerLeft,
                              child: FilledButton.icon(
                                onPressed: () =>
                                    CatalogActions.showEditTeacherDialog(
                                  ctx,
                                  mwalimuId: id,
                                  repo: catalog,
                                  onSaved: reload,
                                ),
                                icon: const Icon(Icons.edit_outlined, size: 18),
                                label: const Text('Hariri Mwalimu'),
                              ),
                            )
                        : null,
                  );
                },
              ),
            ],
          ),
          GoRoute(
            path: '/wanafunzi',
            builder: (context, state) {
              final darasa = state.uri.queryParameters['darasa'];
              return _WanafunziListPage(
                darasa: darasa,
                catalog: catalog,
                canRegister: auth.profile?.canManageStudents ?? false,
              );
            },
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) {
                  final id =
                      int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
                  final tab = state.uri.queryParameters['tab'];
                  final initialIndex = tab == 'rekodi'
                      ? 3
                      : (tab == 'mahudhurio' ? 2 : 0);
                  return StudentDetailView(
                    studentId: id,
                    repository: catalog,
                    initialTabIndex: initialIndex,
                  );
                },
                routes: [
                  GoRoute(
                    path: 'sabaq',
                    builder: (context, state) {
                      final id =
                          int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
                      final aina =
                          state.uri.queryParameters['aina'] ?? 'Usiku';
                      final extra = state.extra;
                      final mwanafunzi =
                          extra is Mwanafunzi ? extra : null;
                      return RekodiSabaqView(
                        mwanafunziId: id,
                        repository: catalog,
                        aina: aina,
                        mwanafunzi: mwanafunzi,
                      );
                    },
                  ),
                ],
              ),
            ],
          ),
          GoRoute(
            path: '/masomo',
            builder: (context, state) => CatalogListView(
              viewModel: CatalogViewModel(loader: ({q}) => catalog.masomo()),
              topBar: (auth.profile?.canManageStudents ?? false)
                  ? (ctx, reload) => CatalogActions.masomoTopBar(
                        context: ctx,
                        repo: catalog,
                        reload: reload,
                      )
                  : null,
            ),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) {
                  final id =
                      int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
                  return SubjectDetailView(
                    somoId: id,
                    repository: catalog,
                  );
                },
                routes: [
                  GoRoute(
                    path: 'mitihani/:mtihaniId',
                    builder: (context, state) {
                      final mtihaniId =
                          int.tryParse(
                            state.pathParameters['mtihaniId'] ?? '',
                          ) ??
                          0;
                      final extra = state.extra;
                      final editable = extra is Map && extra['edit'] == true;
                      return ExamResultsView(
                        mtihaniId: mtihaniId,
                        repository: catalog,
                        editable: editable,
                      );
                    },
                  ),
                  GoRoute(
                    path: 'mahudhurio',
                    builder: (context, state) {
                      final id =
                          int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
                      return RollCallView(
                        viewModel: RollCallViewModel.hifdhu(
                          repository: attendance,
                          somoId: id,
                          canTakeAttendance:
                              auth.profile?.canTakeAttendance ?? false,
                        ),
                      );
                    },
                  ),
                  GoRoute(
                    path: 'wanafunzi',
                    builder: (context, state) {
                      final id =
                          int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
                      return HifdhuStudentsView(
                        somoId: id,
                        repository: catalog,
                      );
                    },
                  ),
                ],
              ),
            ],
          ),
          GoRoute(
            path: '/madarasa',
            builder: (context, state) => ClassesView(
              viewModel: context.read<ClassesViewModel>(),
              canManageClasses: auth.profile?.canManageStudents ?? false,
              catalog: catalog,
            ),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) {
                  final classesVm = context.read<ClassesViewModel>();
                  final darasa = darasaFrom(state, classesVm);
                  if (darasa == null) {
                    return const Center(child: Text('Darasa halipatikani.'));
                  }
                  return ClassHubView(
                    darasa: darasa,
                    catalog: catalog,
                    canTakeAttendance:
                        auth.profile?.canTakeAttendance ?? false,
                    canViewStudents: auth.profile?.canViewStudents ?? false,
                    canViewExams: auth.profile?.canSeeExams ?? false,
                    canRecordExams: auth.profile?.canSeeExams ?? false,
                    canRecordSabaq: auth.profile?.canRecordSabaq ?? false,
                    canManageClasses: auth.profile?.canManageStudents ?? false,
                    onClassUpdated: classesVm.load,
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
                        return const Center(
                          child: Text('Darasa halipatikani.'),
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
                  GoRoute(
                    path: 'wanafunzi',
                    builder: (context, state) {
                      final id =
                          int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
                      final jina = state.uri.queryParameters['jina'];
                      return HifdhuStudentsView(
                        darasaId: id,
                        darasaJina: jina,
                        repository: catalog,
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
              hint: 'Gusa rekodi ya malipo kupakua risiti ya PDF.',
              viewModel: CatalogViewModel(loader: ({q}) => catalog.malipo()),
              onRowTap: (ctx, row, _) => CatalogActions.onMalipoRowTap(
                ctx,
                row,
                repo: catalog,
              ),
            ),
          ),
          GoRoute(
            path: '/aina-malipo',
            builder: (context, state) {
              final canManage = auth.profile?.canSeeMapato ?? false;
              return CatalogListView(
                viewModel: CatalogViewModel(
                  loader: ({q}) => catalog.ainaMalipo(),
                ),
                topBar: canManage
                    ? (ctx, reload) => CatalogActions.ainaMalipoTopBar(
                          context: ctx,
                          repo: catalog,
                          reload: reload,
                        )
                    : null,
                onRowTap: canManage
                    ? (ctx, row, reload) => CatalogActions.showAinaMalipoDialog(
                          ctx,
                          repo: catalog,
                          onSaved: reload,
                          existing: row,
                        )
                    : null,
              );
            },
          ),
          GoRoute(
            path: '/mwaka',
            builder: (context, state) {
              final canManage = auth.profile?.canSeeMwaka ?? false;
              return CatalogListView(
                hint: canManage
                    ? 'Gusa mwaka au muhula kuuweka kuwa hai.'
                    : null,
                viewModel: CatalogViewModel(loader: ({q}) => catalog.mwaka()),
                topBar: canManage
                    ? (ctx, reload) => CatalogActions.mwakaTopBar(
                          context: ctx,
                          repo: catalog,
                          reload: reload,
                        )
                    : null,
                onRowTap: canManage
                    ? (ctx, row, reload) => CatalogActions.onMwakaRowTap(
                          ctx,
                          row,
                          repo: catalog,
                          reload: reload,
                        )
                    : null,
              );
            },
          ),
          GoRoute(
            path: '/hamisha',
            builder: (context, state) {
              final canPromote = auth.profile?.canPromoteClass ?? false;
              return CatalogListView(
                hint: MadrasaCopy.promoteHint,
                viewModel: CatalogViewModel(loader: ({q}) => catalog.hamisha()),
                topBar: canPromote
                    ? (ctx, reload) => CatalogActions.hamishaTopBar(
                          context: ctx,
                          repo: catalog,
                          reload: reload,
                        )
                    : null,
              );
            },
          ),
          GoRoute(
            path: '/mawasiliano',
            builder: (context, state) {
              final canParents = auth.profile?.canSeeParents ?? false;
              return CatalogListView(
                searchable: true,
                viewModel: CatalogViewModel(
                  loader: ({q}) => catalog.mawasiliano(q: q),
                ),
                topBar: canParents
                    ? (ctx, _) => CatalogActions.mawasilianoTopBar(
                          context: ctx,
                          repo: catalog,
                        )
                    : null,
                onRowTap: (ctx, row, _) =>
                    CatalogActions.onMawasilianoRowTap(ctx, row),
              );
            },
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

class _WanafunziListPage extends StatefulWidget {
  const _WanafunziListPage({
    required this.darasa,
    required this.catalog,
    required this.canRegister,
  });

  final String? darasa;
  final CatalogRepository catalog;
  final bool canRegister;

  @override
  State<_WanafunziListPage> createState() => _WanafunziListPageState();
}

class _WanafunziListPageState extends State<_WanafunziListPage> {
  String _hali = 'hai';
  late CatalogViewModel _vm;

  @override
  void initState() {
    super.initState();
    _buildVm();
  }

  @override
  void didUpdateWidget(covariant _WanafunziListPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.darasa != widget.darasa) {
      _buildVm();
    }
  }

  void _buildVm() {
    _vm = CatalogViewModel(
      loader: ({q}) => widget.catalog.wanafunzi(
        q: q,
        darasa: widget.darasa,
        hali: _hali == 'hai' ? null : _hali,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return CatalogListView(
      searchable: true,
      showStudentStats: true,
      viewModel: _vm,
      topBar: (ctx, reload) => CatalogActions.wanafunziTopBar(
        context: ctx,
        repo: widget.catalog,
        canRegister: widget.canRegister,
        currentHali: _hali,
        onSelectHali: (newHali) {
          setState(() {
            _hali = newHali;
            _buildVm();
          });
        },
        reload: reload,
      ),
    );
  }
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
