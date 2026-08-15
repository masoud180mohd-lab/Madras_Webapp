import 'package:flutter_test/flutter_test.dart';
import 'package:madrasa_mobile/data/models/models.dart';
import 'package:madrasa_mobile/ui/core/copy.dart';
import 'package:madrasa_mobile/ui/core/nav.dart';

void main() {
  StaffProfile profile(List<String> caps) {
    return StaffProfile(
      id: 1,
      username: 'u',
      jina: 'Mwalimu',
      cheo: 'Mwalimu wa Kawaida',
      capabilities: caps,
    );
  }

  test('kawaida sees taaluma items but not fees', () {
    final items = navItemsFor(
      profile(['attendance', 'view_students', 'view_directory', 'exams']),
    );
    final labels = items.map((item) => item.label).toList();
    expect(labels, contains(MadrasaCopy.home));
    expect(labels, contains(MadrasaCopy.teachers));
    expect(labels, contains(MadrasaCopy.students));
    expect(labels, contains(MadrasaCopy.subjects));
    expect(labels, contains(MadrasaCopy.classes));
    expect(labels, contains(MadrasaCopy.absentees));
    expect(labels, isNot(contains(MadrasaCopy.payments)));
    expect(labels, isNot(contains(MadrasaCopy.contacts)));
  });

  test('office sees payments and contacts, not teachers', () {
    final items = navItemsFor(profile(['fees', 'parent_contact']));
    final labels = items.map((item) => item.label).toList();
    expect(labels, contains(MadrasaCopy.payments));
    expect(labels, contains(MadrasaCopy.contacts));
    expect(labels, contains(MadrasaCopy.audit));
    expect(labels, isNot(contains(MadrasaCopy.teachers)));
    expect(labels, isNot(contains(MadrasaCopy.classes)));
  });
}
