from .models import Somo, Mtihani, Matokeo, Mwanafunzi


def hesabu_daraja(maksi):
    if maksi >= 81:
        return 'A', 'Vizuri Sana', '#2E7D32'
    if maksi >= 61:
        return 'B', 'Vizuri', '#0288D1'
    if maksi >= 41:
        return 'C', 'Wastani', '#f57c00'
    if maksi >= 31:
        return 'D', 'Dhaifu', '#c2185b'
    return 'F', 'Feli', '#d32f2f'


def jenga_ripoti_jumla(mseto):
    """
    Inajenga ripoti ya jumla ya darasa kwa mseto wa mitihani.
    Inarudisha: masomo, mitihani_map, matokeo_wanafunzi, hali_ya_masomo,
    grade_summary, grade_order
    """
    darasa = mseto.darasa
    masomo = list(
        Somo.objects.filter(darasa=darasa, ni_la_hifdhu=False).order_by('jina')
    )

    mitihani_map = {}
    hali_ya_masomo = []
    mtihani_ids = []
    for somo in masomo:
        mtihani = Mtihani.objects.filter(somo=somo, mseto=mseto).first()
        mitihani_map[somo.id] = mtihani
        if mtihani:
            mtihani_ids.append(mtihani.id)
        idadi_maksi = 0
        if mtihani:
            idadi_maksi = Matokeo.objects.filter(mtihani=mtihani).count()
        hali_ya_masomo.append({
            'somo': somo,
            'mtihani': mtihani,
            'imekamilika': mtihani is not None,
            'idadi_maksi': idadi_maksi,
        })

    matokeo_lookup = {}
    if mtihani_ids:
        for matokeo in Matokeo.objects.filter(mtihani_id__in=mtihani_ids).select_related('mwanafunzi'):
            matokeo_lookup[(matokeo.mwanafunzi_id, matokeo.mtihani_id)] = matokeo

    idadi_ya_mitihani = len(mtihani_ids)
    wanafunzi = Mwanafunzi.objects.filter(darasa=darasa).order_by('jina_kamili')
    matokeo_wanafunzi = []

    for mwanafunzi in wanafunzi:
        masomo_data = []
        jumla = 0
        yaliyojazwa = 0

        for somo in masomo:
            mtihani = mitihani_map.get(somo.id)
            if mtihani:
                matokeo = matokeo_lookup.get((mwanafunzi.id, mtihani.id))
                if matokeo:
                    daraja, maelezo, rangi = hesabu_daraja(matokeo.maksi)
                    masomo_data.append({
                        'somo': somo,
                        'maksi': matokeo.maksi,
                        'daraja': daraja,
                        'maelezo': maelezo,
                        'rangi': rangi,
                        'imejazwa': True,
                    })
                    jumla += matokeo.maksi
                    yaliyojazwa += 1
                else:
                    masomo_data.append({
                        'somo': somo, 'maksi': None, 'daraja': '-',
                        'maelezo': '', 'rangi': '', 'imejazwa': False,
                    })
            else:
                masomo_data.append({
                    'somo': somo, 'maksi': None, 'daraja': '-',
                    'maelezo': 'Hakuna mtihani', 'rangi': '', 'imejazwa': False,
                })

        if idadi_ya_mitihani > 0:
            wastani = round(jumla / idadi_ya_mitihani, 1)
            daraja_jumla, maelezo_jumla, rangi_jumla = hesabu_daraja(wastani)
        else:
            wastani = None
            daraja_jumla, maelezo_jumla, rangi_jumla = '-', '', ''

        matokeo_wanafunzi.append({
            'mwanafunzi': mwanafunzi,
            'masomo': masomo_data,
            'jumla': jumla if yaliyojazwa > 0 else None,
            'wastani': wastani,
            'daraja_jumla': daraja_jumla,
            'maelezo_jumla': maelezo_jumla,
            'rangi_jumla': rangi_jumla,
            'yaliyojazwa': yaliyojazwa,
        })

    matokeo_wanafunzi.sort(
        key=lambda x: (x['wastani'] is not None, x['wastani'] or 0),
        reverse=True,
    )
    nafasi = 1
    for row in matokeo_wanafunzi:
        if row['wastani'] is not None:
            row['nafasi'] = nafasi
            nafasi += 1
        else:
            row['nafasi'] = '-'

    grade_order = ['A', 'B', 'C', 'D', 'F']
    jinsia_rows = [
        ('KE', 'KE'),
        ('ME', 'ME'),
        ('T', 'Jumla'),
    ]
    grade_summary = []
    for jinsia_code, label in jinsia_rows:
        grade_counts = []
        total = 0
        for grade in grade_order:
            if jinsia_code == 'T':
                count = sum(1 for row in matokeo_wanafunzi if row['daraja_jumla'] == grade)
            else:
                count = sum(
                    1 for row in matokeo_wanafunzi
                    if row['mwanafunzi'].jinsia == jinsia_code and row['daraja_jumla'] == grade
                )
            grade_counts.append(count)
            total += count
        grade_summary.append({
            'jinsia': label,
            'grade_counts': grade_counts,
            'total': total,
        })

    return {
        'masomo': masomo,
        'mitihani_map': mitihani_map,
        'matokeo_wanafunzi': matokeo_wanafunzi,
        'hali_ya_masomo': hali_ya_masomo,
        'grade_order': grade_order,
        'grade_summary': grade_summary,
        'idadi_ya_mitihani': idadi_ya_mitihani,
    }
