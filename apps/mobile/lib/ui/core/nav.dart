import '../../data/models/models.dart';
import 'copy.dart';

class NavItem {
  const NavItem({
    required this.path,
    required this.label,
    required this.icon,
    this.section,
  });

  final String path;
  final String label;
  final String icon;
  final String? section;
}

List<NavItem> navItemsFor(StaffProfile? profile) {
  if (profile == null) {
    return const [];
  }
  final items = <NavItem>[
    const NavItem(path: '/mwanzo', label: MadrasaCopy.home, icon: 'home'),
  ];
  if (profile.canSeeTaaluma) {
    if (profile.canViewDirectory) {
      items.add(
        const NavItem(
          path: '/walimu',
          label: MadrasaCopy.teachers,
          icon: 'teachers',
          section: MadrasaCopy.taaluma,
        ),
      );
    }
    if (profile.canViewStudents) {
      items.add(
        const NavItem(
          path: '/wanafunzi',
          label: MadrasaCopy.students,
          icon: 'students',
          section: MadrasaCopy.taaluma,
        ),
      );
    }
    if (profile.canViewDirectory || profile.canSeeExams) {
      items.add(
        const NavItem(
          path: '/masomo',
          label: MadrasaCopy.subjects,
          icon: 'subjects',
          section: MadrasaCopy.taaluma,
        ),
      );
    }
    if (profile.canViewDirectory || profile.canViewStudents) {
      items.add(
        const NavItem(
          path: '/madarasa',
          label: MadrasaCopy.classes,
          icon: 'classes',
          section: MadrasaCopy.taaluma,
        ),
      );
    }
    if (profile.canTakeAttendance || profile.canViewStudents) {
      items.add(
        const NavItem(
          path: '/watoro',
          label: MadrasaCopy.absentees,
          icon: 'absentees',
          section: MadrasaCopy.taaluma,
        ),
      );
    }
  }
  if (profile.canSeeMapato) {
    if (profile.canSeeFees) {
      items.add(
        const NavItem(
          path: '/malipo',
          label: MadrasaCopy.payments,
          icon: 'payments',
          section: MadrasaCopy.revenue,
        ),
      );
    }
    if (profile.canManageStudents) {
      items.add(
        const NavItem(
          path: '/aina-malipo',
          label: MadrasaCopy.feeTypes,
          icon: 'fees',
          section: MadrasaCopy.revenue,
        ),
      );
    }
  }
  if (profile.canSeeMwaka) {
    if (profile.canSeeMseto) {
      items.add(
        const NavItem(
          path: '/mwaka',
          label: MadrasaCopy.yearTerm,
          icon: 'year',
          section: MadrasaCopy.yearSection,
        ),
      );
    }
    if (profile.canPromoteClass) {
      items.add(
        const NavItem(
          path: '/hamisha',
          label: MadrasaCopy.promote,
          icon: 'promote',
          section: MadrasaCopy.yearSection,
        ),
      );
    }
  }
  if (profile.canSeeParents) {
    items.add(
      const NavItem(
        path: '/mawasiliano',
        label: MadrasaCopy.contacts,
        icon: 'contacts',
      ),
    );
  }
  if (profile.canSeeAudit) {
    items.add(
      const NavItem(path: '/ukaguzi', label: MadrasaCopy.audit, icon: 'audit'),
    );
  }
  items.add(
    const NavItem(
      path: '/mipangilio',
      label: MadrasaCopy.settings,
      icon: 'settings',
    ),
  );
  return items;
}

String titleForPath(String path) {
  if (path.contains('/mahudhurio')) {
    return MadrasaCopy.rollCall;
  }
  if (path.startsWith('/madarasa/')) {
    return MadrasaCopy.classes;
  }
  switch (path) {
    case '/mwanzo':
      return MadrasaCopy.home;
    case '/walimu':
      return MadrasaCopy.teachers;
    case '/wanafunzi':
      return MadrasaCopy.students;
    case '/masomo':
      return MadrasaCopy.subjects;
    case '/madarasa':
      return MadrasaCopy.classes;
    case '/watoro':
      return MadrasaCopy.absentees;
    case '/malipo':
      return MadrasaCopy.payments;
    case '/aina-malipo':
      return MadrasaCopy.feeTypes;
    case '/mwaka':
      return MadrasaCopy.yearTerm;
    case '/hamisha':
      return MadrasaCopy.promote;
    case '/mawasiliano':
      return MadrasaCopy.contacts;
    case '/ukaguzi':
      return MadrasaCopy.audit;
    case '/mipangilio':
      return MadrasaCopy.settings;
    default:
      if (path.startsWith('/wanafunzi/')) {
        return MadrasaCopy.studentDetail;
      }
      return MadrasaCopy.brand;
  }
}
