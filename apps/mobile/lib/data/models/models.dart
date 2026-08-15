class TokenPair {
  const TokenPair({required this.access, required this.refresh});

  final String access;
  final String refresh;

  factory TokenPair.fromJson(Map<String, dynamic> json) {
    final access = json['access'];
    final refresh = json['refresh'];
    if (access is! String || refresh is! String) {
      throw const FormatException('Token si sahihi.');
    }
    return TokenPair(access: access, refresh: refresh);
  }
}

class StaffProfile {
  const StaffProfile({
    required this.id,
    required this.username,
    required this.jina,
    required this.cheo,
    required this.capabilities,
  });

  final int id;
  final String username;
  final String jina;
  final String? cheo;
  final List<String> capabilities;

  bool get canViewDirectory => capabilities.contains('view_directory');
  bool get canViewStudents => capabilities.contains('view_students');
  bool get canTakeAttendance => capabilities.contains('attendance');
  bool get canManageStudents => capabilities.contains('manage_students');
  bool get canSeeFees => capabilities.contains('fees');
  bool get canSeeExams => capabilities.contains('exams');
  bool get canSeeMseto => capabilities.contains('mseto');
  bool get canPromoteClass => capabilities.contains('promote_class');
  bool get canSeeParents => capabilities.contains('parent_contact');
  bool get canSeeAudit => canManageStudents || canSeeFees;
  bool get canSeeTaaluma =>
      canViewStudents || canViewDirectory || canSeeExams || canTakeAttendance;
  bool get canSeeMapato => canSeeFees || canManageStudents;
  bool get canSeeMwaka => canSeeMseto || canPromoteClass;

  factory StaffProfile.fromJson(Map<String, dynamic> json) {
    final caps = json['capabilities'];
    return StaffProfile(
      id: json['id'] as int,
      username: json['username'] as String,
      jina: json['jina'] as String,
      cheo: json['cheo'] as String?,
      capabilities: caps is List
          ? caps.whereType<String>().toList(growable: false)
          : const <String>[],
    );
  }
}

class Darasa {
  const Darasa({
    required this.id,
    required this.jina,
    this.maelezo,
    this.idadiWanafunzi,
  });

  final int id;
  final String jina;
  final String? maelezo;
  final int? idadiWanafunzi;

  factory Darasa.fromJson(Map<String, dynamic> json) {
    return Darasa(
      id: json['id'] as int,
      jina: json['jina'] as String,
      maelezo: json['maelezo'] as String?,
      idadiWanafunzi: json['idadi_wanafunzi'] as int?,
    );
  }
}

class DashboardMetric {
  const DashboardMetric({
    required this.label,
    required this.value,
    this.hint,
    this.tone = 'ok',
  });

  final String label;
  final String value;
  final String? hint;
  final String tone;

  factory DashboardMetric.fromJson(Map<String, dynamic> json) {
    return DashboardMetric(
      label: json['label'] as String,
      value: '${json['value']}',
      hint: json['hint'] as String?,
      tone: json['tone'] as String? ?? 'ok',
    );
  }
}

class DashboardSnapshot {
  const DashboardSnapshot({
    required this.jina,
    this.cheo,
    required this.leo,
    required this.vipimo,
    required this.matangazo,
  });

  final String jina;
  final String? cheo;
  final String leo;
  final List<DashboardMetric> vipimo;
  final List<CatalogRow> matangazo;

  factory DashboardSnapshot.fromJson(Map<String, dynamic> json) {
    final vipimo = json['vipimo'];
    final matangazo = json['matangazo'];
    return DashboardSnapshot(
      jina: json['jina'] as String,
      cheo: json['cheo'] as String?,
      leo: json['leo'] as String? ?? '',
      vipimo: vipimo is List
          ? vipimo
                .whereType<Map<String, dynamic>>()
                .map(DashboardMetric.fromJson)
                .toList(growable: false)
          : const [],
      matangazo: matangazo is List
          ? matangazo.whereType<Map<String, dynamic>>().map((row) {
              return CatalogRow(
                title: row['kichwa_cha_habari'] as String? ?? '',
                subtitle: row['maelezo'] as String?,
              );
            }).toList(growable: false)
          : const [],
    );
  }
}

class CatalogRow {
  const CatalogRow({required this.title, this.subtitle, this.trailing});

  final String title;
  final String? subtitle;
  final String? trailing;
}

class Mwanafunzi {
  const Mwanafunzi({
    required this.id,
    required this.jinaKamili,
    required this.nambaYaUsajili,
    required this.jinsia,
    this.pichaUrl,
  });

  final int id;
  final String jinaKamili;
  final String nambaYaUsajili;
  final String jinsia;
  final String? pichaUrl;

  factory Mwanafunzi.fromJson(Map<String, dynamic> json) {
    return Mwanafunzi(
      id: json['id'] as int,
      jinaKamili: json['jina_kamili'] as String,
      nambaYaUsajili: json['namba_ya_usajili'] as String,
      jinsia: json['jinsia'] as String? ?? 'ME',
      pichaUrl: json['picha'] as String?,
    );
  }
}

class Hudhurio {
  const Hudhurio({
    required this.mwanafunziId,
    required this.yupo,
    required this.tarehe,
    this.sababuKamaHayupo,
  });

  final int mwanafunziId;
  final bool yupo;
  final String tarehe;
  final String? sababuKamaHayupo;

  factory Hudhurio.fromJson(Map<String, dynamic> json) {
    return Hudhurio(
      mwanafunziId: json['mwanafunzi'] as int,
      yupo: json['yupo'] as bool,
      tarehe: json['tarehe'] as String,
      sababuKamaHayupo: json['sababu_kama_hayupo'] as String?,
    );
  }
}

class RollDraft {
  RollDraft({
    required this.mwanafunzi,
    required this.yupo,
    this.sababu = '',
  });

  final Mwanafunzi mwanafunzi;
  bool yupo;
  String sababu;

  Map<String, dynamic> toJson() {
    return {
      'mwanafunzi': mwanafunzi.id,
      'yupo': yupo,
      'sababu_kama_hayupo': yupo ? '' : sababu,
    };
  }
}
