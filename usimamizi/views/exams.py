import csv
import os
from urllib.parse import urlparse
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.timezone import localtime
from django.urls import reverse

from ..models import Mwanafunzi, Hudhurio, Tangazo, Mwalimu, Darasa, Somo, Nyenzo, Mtihani, Matokeo, RekodiHifdhu, PandeMurajaa, AinaMalipo, Malipo, MsetoMtihani
from ..forms import (
    MwanafunziForm,
    NyenzoForm,
    MtihaniForm,
    MsetoMtihaniForm,
    MalipoForm,
    SabaqRekodiForm,
    parse_mapande_from_post,
    parse_maksi_post,
    build_hudhurio_rows,
)
from ..utils import hesabu_daraja, jenga_ripoti_jumla
from ..permissions import (
    CAP_ATTENDANCE,
    CAP_EXAMS,
    CAP_FEES,
    CAP_MANAGE_STUDENTS,
    CAP_MATERIALS,
    CAP_MSETO,
    CAP_SABAQ,
    CAP_VIEW_DIRECTORY,
    CAP_VIEW_STUDENTS,
    linked_mwalimu_or_none,
    require_linked_mwalimu,
    ruhusa_capability,
    ruhusa_inahitajika,
    user_has_app_permission,
    user_has_capability,
)

from .helpers import link_callback

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.add_matokeo', 'usimamizi.change_matokeo')
def weka_maksi(request, mtihani_id):
    mtihani = get_object_or_404(Mtihani, id=mtihani_id)
    somo = mtihani.somo

    if somo.darasa:
        wanafunzi = Mwanafunzi.objects.filter(darasa=somo.darasa).select_related('darasa').order_by('jina_kamili')
    else:
        wanafunzi = Mwanafunzi.objects.select_related('darasa').all().order_by('jina_kamili')

    if request.method == 'POST':
        scores, errors = parse_maksi_post(wanafunzi, request.POST)
        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect('weka_maksi', mtihani_id=mtihani.id)
        for mwanafunzi_id, maksi_value in scores.items():
            Matokeo.objects.update_or_create(
                mwanafunzi_id=mwanafunzi_id,
                mtihani=mtihani,
                defaults={'maksi': maksi_value},
            )
        messages.success(request, f'✅ Maksi za mtihani "{mtihani.jina_la_mtihani}" zimehifadhiwa!')
        return redirect('somo_detail', somo_id=somo.id)

    existing = {
        row.mwanafunzi_id: row.maksi
        for row in Matokeo.objects.filter(mtihani=mtihani, mwanafunzi__in=wanafunzi)
    }
    for mwanafunzi in wanafunzi:
        mwanafunzi.maksi_yake = existing.get(mwanafunzi.id, "")

    return render(request, 'usimamizi/weka_maksi.html', {
        'mtihani': mtihani,
        'somo': somo,
        'wanafunzi': wanafunzi
    })

@login_required(login_url='ingia')
@ruhusa_capability(CAP_EXAMS)
def tazama_matokeo(request, mtihani_id):
    mtihani = get_object_or_404(Mtihani, id=mtihani_id)
    somo = mtihani.somo

    # Tunavuta matokeo na kupanga kuanzia Maksi kubwa kwenda ndogo (Ranking)
    matokeo_yote = (
        Matokeo.objects.filter(mtihani=mtihani)
        .select_related('mwanafunzi')
        .order_by('-maksi')
    )

    # Tunatengeneza list mpya itakayobeba matokeo + daraja + nafasi
    orodha_iliyopangwa = []
    nafasi = 1

    for matokeo in matokeo_yote:
        daraja, maelezo, rangi = hesabu_daraja(matokeo.maksi)
        orodha_iliyopangwa.append({
            'mwanafunzi': matokeo.mwanafunzi,
            'maksi': matokeo.maksi,
            'daraja': daraja,
            'rangi': rangi,
            'maelezo': maelezo,
            'nafasi': nafasi
        })
        nafasi += 1

    return render(request, 'usimamizi/tazama_matokeo.html', {
        'mtihani': mtihani,
        'somo': somo,
        'matokeo': orodha_iliyopangwa,
        'idadi_waliofanya': matokeo_yote.count()
    })

@login_required(login_url='ingia')
@ruhusa_capability(CAP_EXAMS)
def pakua_pdf_matokeo(request, mtihani_id):
    mtihani = get_object_or_404(Mtihani, id=mtihani_id)
    somo = mtihani.somo
    matokeo_yote = (
        Matokeo.objects.filter(mtihani=mtihani)
        .select_related('mwanafunzi')
        .order_by('-maksi')
    )

    orodha_iliyopangwa = []
    nafasi = 1

    for matokeo in matokeo_yote:
        daraja, maelezo, _ = hesabu_daraja(matokeo.maksi)
        orodha_iliyopangwa.append({
            'mwanafunzi': matokeo.mwanafunzi,
            'maksi': matokeo.maksi,
            'daraja': daraja,
            'maelezo': maelezo,
            'nafasi': nafasi
        })
        nafasi += 1

    context = {
        'mtihani': mtihani,
        'somo': somo,
        'matokeo': orodha_iliyopangwa,
        'idadi_waliofanya': matokeo_yote.count(),
        'wakati_huu': localtime(timezone.now())
    }

    template = get_template('usimamizi/pdf_matokeo.html')
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    jina_la_faili = f"Matokeo_{somo.jina}_{mtihani.jina_la_mtihani}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{jina_la_faili}"'

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse('Kumetokea hitilafu katika kutengeneza PDF ya matokeo', status=500)
    return response

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.add_msetomtihani')
def mseto_mitihani_darasa(request, darasa_id):
    darasa = get_object_or_404(Darasa, id=darasa_id)
    mseto_zote = MsetoMtihani.objects.filter(darasa=darasa).prefetch_related('mitihani__somo')

    if request.method == 'POST':
        form = MsetoMtihaniForm(request.POST)
        if form.is_valid():
            mseto = form.save(commit=False)
            mseto.darasa = darasa
            mseto.save()
            messages.success(request, f'✅ Mseto "{mseto.jina}" umeundwa kikamilifu!')
            return redirect('mseto_mitihani_darasa', darasa_id=darasa.id)
    else:
        form = MsetoMtihaniForm()

    mseto_na_hali = []
    masomo_count = Somo.objects.filter(darasa=darasa, ni_la_hifdhu=False).count()
    for mseto in mseto_zote:
        mitihani_iliyounganishwa = mseto.mitihani.count()
        mseto_na_hali.append({
            'mseto': mseto,
            'mitihani_iliyounganishwa': mitihani_iliyounganishwa,
            'jumla_masomo': masomo_count,
        })

    return render(request, 'usimamizi/mseto_mitihani.html', {
        'darasa': darasa,
        'form': form,
        'mseto_na_hali': mseto_na_hali,
        'masomo_count': masomo_count,
    })

@login_required(login_url='ingia')
@ruhusa_capability(CAP_MSETO, CAP_EXAMS)
def ripoti_jumla(request, darasa_id, mseto_id):
    darasa = get_object_or_404(Darasa, id=darasa_id)
    mseto = get_object_or_404(MsetoMtihani, id=mseto_id, darasa=darasa)
    ripoti = jenga_ripoti_jumla(mseto)

    return render(request, 'usimamizi/ripoti_jumla.html', {
        'darasa': darasa,
        'mseto': mseto,
        **ripoti,
    })

@login_required(login_url='ingia')
@ruhusa_capability(CAP_MSETO, CAP_EXAMS)
def pakua_pdf_matokeo_jumla(request, darasa_id, mseto_id):
    darasa = get_object_or_404(Darasa, id=darasa_id)
    mseto = get_object_or_404(MsetoMtihani, id=mseto_id, darasa=darasa)
    ripoti = jenga_ripoti_jumla(mseto)
    for somo in ripoti['masomo']:
        somo.jina_pdf = somo.jina.replace('_', ' ')

    context = {
        'darasa': darasa,
        'mseto': mseto,
        'wakati_huu': localtime(timezone.now()),
        **ripoti,
    }

    template = get_template('usimamizi/pdf_matokeo_jumla.html')
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    jina_salama = mseto.jina.replace(' ', '_')
    jina_la_faili = f"Matokeo_Jumla_{darasa.jina}_{jina_salama}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{jina_la_faili}"'

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse('Kumetokea hitilafu katika kutengeneza PDF ya matokeo ya jumla', status=500)
    return response

@login_required(login_url='ingia')
@ruhusa_capability(CAP_MSETO, CAP_EXAMS)
def pakua_csv_matokeo_jumla(request, darasa_id, mseto_id):
    darasa = get_object_or_404(Darasa, id=darasa_id)
    mseto = get_object_or_404(MsetoMtihani, id=mseto_id, darasa=darasa)
    ripoti = jenga_ripoti_jumla(mseto)
    masomo = ripoti['masomo']

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    jina_salama = mseto.jina.replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="Matokeo_Jumla_{darasa.jina}_{jina_salama}.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Muhtasari wa Grade kwa Jinsia'])
    summary_header = ['Jinsia'] + ripoti['grade_order'] + ['Jumla']
    writer.writerow(summary_header)
    for summary_row in ripoti['grade_summary']:
        writer.writerow([summary_row['jinsia']] + summary_row['grade_counts'] + [summary_row['total']])
    writer.writerow([])

    header = ['Nafasi', 'Namba ya Usajili', 'Jina la Mwanafunzi']
    header += [s.jina for s in masomo]
    header += ['Wastani', 'Daraja']
    writer.writerow(header)

    for row in ripoti['matokeo_wanafunzi']:
        line = [
            row['nafasi'],
            row['mwanafunzi'].namba_ya_usajili,
            row['mwanafunzi'].jina_kamili,
        ]
        for somo_data in row['masomo']:
            if somo_data['imejazwa']:
                line.append(f"{somo_data['maksi']:.0f} ({somo_data['daraja']})")
            else:
                line.append('-')
        line.append(row['wastani'] if row['wastani'] is not None else '-')
        line.append(row['daraja_jumla'])
        writer.writerow(line)

    return response

