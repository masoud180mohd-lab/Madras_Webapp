import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/view_models/auth_view_model.dart';
import '../copy.dart';
import '../nav.dart';
import '../theme.dart';

class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.auth, required this.child});

  final AuthViewModel auth;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final path = GoRouterState.of(context).uri.path;
    return Scaffold(
      appBar: AppBar(
        title: Text(titleForPath(path)),
      ),
      drawer: AppDrawer(auth: auth, currentPath: path),
      body: child,
    );
  }
}

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key, required this.auth, required this.currentPath});

  final AuthViewModel auth;
  final String currentPath;

  @override
  Widget build(BuildContext context) {
    final profile = auth.profile;
    final items = navItemsFor(profile);
    final sections = <String?>[];
    for (final item in items) {
      if (!sections.contains(item.section)) {
        sections.add(item.section);
      }
    }

    return Drawer(
      backgroundColor: MadrasaTheme.forest,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 20, 20, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    MadrasaCopy.location,
                    style: TextStyle(
                      color: Color(0xFFD4A84B),
                      fontSize: 12,
                      letterSpacing: 1.1,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    MadrasaCopy.brand,
                    style: TextStyle(
                      fontFamily: MadrasaTheme.brandFont,
                      color: Color(0xFFF7FAF8),
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
            const Divider(color: Color(0x33FFFFFF), height: 1),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: [
                  for (final section in sections)
                    if (section == null)
                      ...items
                          .where((item) => item.section == null)
                          .map((item) => _NavTile(
                                item: item,
                                selected: _isActive(currentPath, item.path),
                              ))
                    else
                      _Section(
                        title: section,
                        items: items
                            .where((item) => item.section == section)
                            .toList(),
                        currentPath: currentPath,
                      ),
                ],
              ),
            ),
            const Divider(color: Color(0x33FFFFFF), height: 1),
            ListTile(
              leading: const Icon(Icons.logout, color: Color(0xFFFFC9C9)),
              title: const Text(
                MadrasaCopy.logout,
                style: TextStyle(
                  color: Color(0xFFFFC9C9),
                  fontWeight: FontWeight.w600,
                ),
              ),
              onTap: () {
                Navigator.of(context).pop();
                auth.logout();
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({
    required this.title,
    required this.items,
    required this.currentPath,
  });

  final String title;
  final List<NavItem> items;
  final String currentPath;

  @override
  Widget build(BuildContext context) {
    final open = items.any((item) => _isActive(currentPath, item.path));
    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        initiallyExpanded: open,
        iconColor: const Color(0xFFE8EEE9),
        collapsedIconColor: const Color(0xFFE8EEE9),
        leading: Icon(_sectionIcon(title), color: const Color(0xFFE8EEE9)),
        title: Text(
          title,
          style: const TextStyle(
            color: Color(0xFFE8EEE9),
            fontWeight: FontWeight.w600,
            fontSize: 15,
          ),
        ),
        children: [
          for (final item in items)
            _NavTile(
              item: item,
              selected: _isActive(currentPath, item.path),
              indented: true,
            ),
        ],
      ),
    );
  }
}

class _NavTile extends StatelessWidget {
  const _NavTile({
    required this.item,
    required this.selected,
    this.indented = false,
  });

  final NavItem item;
  final bool selected;
  final bool indented;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: selected ? const Color(0x14FFFFFF) : Colors.transparent,
        border: selected
            ? const Border(
                left: BorderSide(color: MadrasaTheme.goldEdge, width: 4),
              )
            : null,
      ),
      child: ListTile(
        contentPadding: EdgeInsets.only(left: indented ? 28 : 16, right: 16),
        leading: Icon(_itemIcon(item.icon), color: const Color(0xFFE8EEE9)),
        title: Text(
          item.label,
          style: const TextStyle(
            color: Color(0xFFE8EEE9),
            fontWeight: FontWeight.w600,
            fontSize: 15,
          ),
        ),
        onTap: () {
          Navigator.of(context).pop();
          context.go(item.path);
        },
      ),
    );
  }
}

bool _isActive(String current, String target) {
  if (current == target) {
    return true;
  }
  return target != '/mwanzo' && current.startsWith('$target/');
}

IconData _sectionIcon(String title) {
  switch (title) {
    case MadrasaCopy.taaluma:
      return Icons.menu_book_outlined;
    case MadrasaCopy.revenue:
      return Icons.credit_card;
    case MadrasaCopy.yearSection:
      return Icons.calendar_month_outlined;
    default:
      return Icons.folder_outlined;
  }
}

IconData _itemIcon(String name) {
  switch (name) {
    case 'home':
      return Icons.home_outlined;
    case 'teachers':
      return Icons.groups_outlined;
    case 'students':
      return Icons.person_outline;
    case 'subjects':
      return Icons.auto_stories_outlined;
    case 'classes':
      return Icons.school_outlined;
    case 'absentees':
      return Icons.flag_outlined;
    case 'payments':
      return Icons.payments_outlined;
    case 'fees':
      return Icons.attach_money;
    case 'year':
      return Icons.event_outlined;
    case 'promote':
      return Icons.swap_horiz;
    case 'contacts':
      return Icons.phone_outlined;
    case 'audit':
      return Icons.fact_check_outlined;
    default:
      return Icons.circle_outlined;
  }
}
