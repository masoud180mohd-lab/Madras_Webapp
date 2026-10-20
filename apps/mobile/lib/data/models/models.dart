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
  bool get canSeeMaterials => capabilities.contains('materials');
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
    this.wavulana,
    this.wasichana,
  });

  final int id;
  final String jina;
  final String? maelezo;
  final int? idadiWanafunzi;
  final int? wavulana;
  final int? wasichana;

  factory Darasa.fromJson(Map<String, dynamic> json) {
    return Darasa(
      id: json['id'] as int,
      jina: json['jina'] as String,
      maelezo: json['maelezo'] as String?,
      idadiWanafunzi: json['idadi_wanafunzi'] as int?,
      wavulana: json['wavulana'] as int?,
      wasichana: json['wasichana'] as int?,
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

class StudentCounts {
  const StudentCounts({
    required this.jumla,
    required this.wavulana,
    required this.wasichana,
  });

  final int jumla;
  final int wavulana;
  final int wasichana;

  factory StudentCounts.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const StudentCounts(jumla: 0, wavulana: 0, wasichana: 0);
    }
    return StudentCounts(
      jumla: json['jumla'] as int? ?? 0,
      wavulana: json['wavulana'] as int? ?? 0,
      wasichana: json['wasichana'] as int? ?? 0,
    );
  }
}

class DashboardSnapshot {
  const DashboardSnapshot({
    required this.jina,
    this.cheo,
    required this.leo,
    required this.idadi,
    required this.vipimo,
    required this.matangazo,
  });

  final String jina;
  final String? cheo;
  final String leo;
  final StudentCounts idadi;
  final List<DashboardMetric> vipimo;
  final List<CatalogRow> matangazo;

  factory DashboardSnapshot.fromJson(Map<String, dynamic> json) {
    final vipimo = json['vipimo'];
    final matangazo = json['matangazo'];
    return DashboardSnapshot(
      jina: json['jina'] as String,
      cheo: json['cheo'] as String?,
      leo: json['leo'] as String? ?? '',
      idadi: StudentCounts.fromJson(
        json['idadi_wanafunzi'] as Map<String, dynamic>?,
      ),
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
  const CatalogRow({
    required this.title,
    this.id,
    this.subtitle,
    this.trailing,
    this.photoUrl,
    this.badge,
    this.detailPath,
    this.isHeader = false,
  });

  final int? id;
  final String title;
  final String? subtitle;
  final String? trailing;
  final String? photoUrl;
  final String? badge;
  final String? detailPath;
  final bool isHeader;
}

class StudentDetail {
  const StudentDetail({
    required this.id,
    required this.jinaKamili,
    required this.nambaYaUsajili,
    required this.jinsia,
    this.darasa,
    this.pichaUrl,
    this.tareheKuzaliwa,
    this.mahala,
    this.programuUsiku,
    this.juzuu,
    this.tareheKujiunga,
    this.jinaMzazi,
    this.simuMzazi,
    this.uhusiano,
    this.jinaMzaziPili,
    this.simuMzaziPili,
    this.uhusianoPili,
  });

  final int id;
  final String jinaKamili;
  final String nambaYaUsajili;
  final String jinsia;
  final String? darasa;
  final String? pichaUrl;
  final String? tareheKuzaliwa;
  final String? mahala;
  final String? programuUsiku;
  final int? juzuu;
  final String? tareheKujiunga;
  final String? jinaMzazi;
  final String? simuMzazi;
  final String? uhusiano;
  final String? jinaMzaziPili;
  final String? simuMzaziPili;
  final String? uhusianoPili;

  factory StudentDetail.fromJson(Map<String, dynamic> json) {
    return StudentDetail(
      id: json['id'] as int,
      jinaKamili: json['jina_kamili'] as String? ?? '',
      nambaYaUsajili: json['namba_ya_usajili'] as String? ?? '',
      jinsia: json['jinsia'] as String? ?? 'ME',
      darasa: json['darasa'] as String?,
      pichaUrl: json['picha'] as String?,
      tareheKuzaliwa: json['tarehe_ya_kuzaliwa'] as String?,
      mahala: json['mahala_anapoishi'] as String?,
      programuUsiku: json['programu_usiku'] as String?,
      juzuu: json['juzuu_aliyohifadhi'] as int?,
      tareheKujiunga: json['tarehe_ya_kujiunga'] as String?,
      jinaMzazi: json['jina_la_mzazi'] as String?,
      simuMzazi: json['namba_ya_simu_mzazi'] as String?,
      uhusiano: json['uhusiano_wa_mlezi'] as String?,
      jinaMzaziPili: json['jina_la_mzazi_pili'] as String?,
      simuMzaziPili: json['namba_ya_simu_mzazi_pili'] as String?,
      uhusianoPili: json['uhusiano_wa_mlezi_pili'] as String?,
    );
  }
}

/// Muhtasari tab of the student profile (`/wanafunzi/<id>/tab/`).
class StudentOverview {
  const StudentOverview({
    required this.mwanafunzi,
    required this.jumlaMalipo,
    required this.idadiMalipo,
    required this.mahudhurioMchana,
    required this.mahudhurioHifdhu,
    required this.idadiSabaq,
    required this.idadiMaendeleo,
  });

  final StudentDetail mwanafunzi;
  final String jumlaMalipo;
  final int idadiMalipo;
  final int mahudhurioMchana;
  final int mahudhurioHifdhu;
  final int idadiSabaq;
  final int idadiMaendeleo;

  factory StudentOverview.fromJson(Map<String, dynamic> json) {
    final m = json['muhtasari'] as Map<String, dynamic>? ?? const {};
    return StudentOverview(
      mwanafunzi: StudentDetail.fromJson(
        json['mwanafunzi'] as Map<String, dynamic>,
      ),
      jumlaMalipo: '${m['jumla_malipo'] ?? 0}',
      idadiMalipo: m['idadi_malipo'] as int? ?? 0,
      mahudhurioMchana: m['mahudhurio_mchana'] as int? ?? 0,
      mahudhurioHifdhu: m['mahudhurio_hifdhu'] as int? ?? 0,
      idadiSabaq: m['idadi_sabaq'] as int? ?? 0,
      idadiMaendeleo: m['idadi_maendeleo'] as int? ?? 0,
    );
  }
}

class StudentPayment {
  const StudentPayment({
    required this.tarehe,
    required this.aina,
    required this.kiasi,
    this.njia,
    this.alirekodi,
  });

  final String tarehe;
  final String aina;
  final String kiasi;
  final String? njia;
  final String? alirekodi;

  factory StudentPayment.fromJson(Map<String, dynamic> json) {
    return StudentPayment(
      tarehe: json['tarehe'] as String? ?? '',
      aina: json['aina'] as String? ?? '',
      kiasi: '${json['kiasi'] ?? 0}',
      njia: json['njia'] as String?,
      alirekodi: json['alirekodi'] as String?,
    );
  }
}

class StudentPayments {
  const StudentPayments({required this.jumla, required this.malipo});

  final String jumla;
  final List<StudentPayment> malipo;

  factory StudentPayments.fromJson(Map<String, dynamic> json) {
    final rows = json['malipo'];
    return StudentPayments(
      jumla: '${json['jumla_malipo'] ?? 0}',
      malipo: rows is List
          ? rows
                .whereType<Map<String, dynamic>>()
                .map(StudentPayment.fromJson)
                .toList(growable: false)
          : const [],
    );
  }
}

class StudentAttendanceDay {
  const StudentAttendanceDay({required this.tarehe, required this.yupo});

  final String tarehe;
  final bool yupo;

  factory StudentAttendanceDay.fromJson(Map<String, dynamic> json) {
    return StudentAttendanceDay(
      tarehe: json['tarehe'] as String? ?? '',
      yupo: json['yupo'] == true,
    );
  }
}

/// Latest attendance rows (up to 12 each) for the Mahudhurio tab.
class StudentAttendance {
  const StudentAttendance({required this.kawaida, required this.hifdhu});

  final List<StudentAttendanceDay> kawaida;
  final List<StudentAttendanceDay> hifdhu;

  factory StudentAttendance.fromJson(Map<String, dynamic> json) {
    return StudentAttendance(
      kawaida: _rows(json['kawaida'], StudentAttendanceDay.fromJson),
      hifdhu: _rows(json['hifdhu'], StudentAttendanceDay.fromJson),
    );
  }
}

/// One Sabaq or daytime-progress row; [kichwa] is the surah or subject.
class StudentRecord {
  const StudentRecord({
    required this.tarehe,
    required this.kichwa,
    required this.hali,
    this.maelezo,
  });

  final String tarehe;
  final String kichwa;
  final String hali;
  final String? maelezo;
}

class StudentRecords {
  const StudentRecords({
    required this.sabaqDarasa,
    required this.sabaqUsiku,
    required this.maendeleo,
  });

  final List<StudentRecord> sabaqDarasa;
  final List<StudentRecord> sabaqUsiku;
  final List<StudentRecord> maendeleo;

  factory StudentRecords.fromJson(Map<String, dynamic> json) {
    StudentRecord sabaq(Map<String, dynamic> row) => StudentRecord(
      tarehe: row['tarehe'] as String? ?? '',
      kichwa: row['sura'] as String? ?? '-',
      hali: row['hali'] as String? ?? '-',
      maelezo: row['somo'] as String?,
    );
    return StudentRecords(
      sabaqDarasa: _rows(json['sabaq_darasa'], sabaq),
      sabaqUsiku: _rows(json['sabaq_usiku'], sabaq),
      maendeleo: _rows(
        json['maendeleo_mchana'],
        (row) => StudentRecord(
          tarehe: row['tarehe'] as String? ?? '',
          kichwa: row['somo'] as String? ?? '-',
          hali: row['hali'] as String? ?? '-',
          maelezo: row['mada'] as String?,
        ),
      ),
    );
  }
}

List<T> _rows<T>(Object? raw, T Function(Map<String, dynamic>) parse) {
  if (raw is! List) {
    return const [];
  }
  return raw
      .whereType<Map<String, dynamic>>()
      .map(parse)
      .toList(growable: false);
}

class SubjectMaterial {
  const SubjectMaterial({
    required this.id,
    required this.jinaLaFaili,
    this.failiUrl,
    this.tarehe,
  });

  final int id;
  final String jinaLaFaili;
  final String? failiUrl;
  final String? tarehe;

  factory SubjectMaterial.fromJson(Map<String, dynamic> json) {
    return SubjectMaterial(
      id: json['id'] as int,
      jinaLaFaili: json['jina_la_faili'] as String? ?? '',
      failiUrl: json['faili'] as String?,
      tarehe: json['tarehe_iliyowekwa'] as String?,
    );
  }
}

class SubjectExam {
  const SubjectExam({
    required this.id,
    required this.jina,
    required this.tarehe,
    required this.somoId,
  });

  final int id;
  final String jina;
  final String tarehe;
  final int somoId;

  factory SubjectExam.fromJson(Map<String, dynamic> json) {
    return SubjectExam(
      id: json['id'] as int,
      jina: json['jina_la_mtihani'] as String? ?? '',
      tarehe: json['tarehe'] as String? ?? '',
      somoId: json['somo'] as int? ?? 0,
    );
  }
}

class SubjectDetail {
  const SubjectDetail({
    required this.id,
    required this.jina,
    required this.niLaHifdhu,
    this.darasaJina,
    this.mwalimu,
    this.nyenzo = const [],
    this.mitihani = const [],
  });

  final int id;
  final String jina;
  final bool niLaHifdhu;
  final String? darasaJina;
  final String? mwalimu;
  final List<SubjectMaterial> nyenzo;
  final List<SubjectExam> mitihani;

  factory SubjectDetail.fromJson(Map<String, dynamic> json) {
    final nyenzo = json['nyenzo'];
    final mitihani = json['mitihani'];
    return SubjectDetail(
      id: json['id'] as int,
      jina: json['jina'] as String? ?? '',
      niLaHifdhu: json['ni_la_hifdhu'] == true,
      darasaJina: json['darasa_jina'] as String?,
      mwalimu: json['mwalimu'] as String?,
      nyenzo: nyenzo is List
          ? nyenzo
                .whereType<Map<String, dynamic>>()
                .map(SubjectMaterial.fromJson)
                .toList(growable: false)
          : const [],
      mitihani: mitihani is List
          ? mitihani
                .whereType<Map<String, dynamic>>()
                .map(SubjectExam.fromJson)
                .toList(growable: false)
          : const [],
    );
  }
}

class ExamMarkRow {
  const ExamMarkRow({
    required this.mwanafunziId,
    required this.jinaKamili,
    this.nambaYaUsajili,
    this.maksi,
    this.daraja,
    this.maelezo,
  });

  final int mwanafunziId;
  final String jinaKamili;
  final String? nambaYaUsajili;
  final double? maksi;
  final String? daraja;
  final String? maelezo;

  factory ExamMarkRow.fromJson(Map<String, dynamic> json) {
    final raw = json['maksi'];
    return ExamMarkRow(
      mwanafunziId: json['mwanafunzi'] as int,
      jinaKamili: json['jina_kamili'] as String? ?? '',
      nambaYaUsajili: json['namba_ya_usajili'] as String?,
      maksi: raw == null ? null : (raw as num).toDouble(),
      daraja: json['daraja'] as String?,
      maelezo: json['maelezo'] as String?,
    );
  }
}

class ExamResults {
  const ExamResults({
    required this.mtihaniId,
    required this.jina,
    required this.tarehe,
    required this.rekodi,
  });

  final int mtihaniId;
  final String jina;
  final String tarehe;
  final List<ExamMarkRow> rekodi;

  factory ExamResults.fromJson(Map<String, dynamic> json) {
    final mtihani = json['mtihani'] as Map<String, dynamic>? ?? const {};
    final rekodi = json['rekodi'];
    return ExamResults(
      mtihaniId: mtihani['id'] as int? ?? 0,
      jina: mtihani['jina_la_mtihani'] as String? ?? '',
      tarehe: mtihani['tarehe'] as String? ?? '',
      rekodi: rekodi is List
          ? rekodi
                .whereType<Map<String, dynamic>>()
                .map(ExamMarkRow.fromJson)
                .toList(growable: false)
          : const [],
    );
  }
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
