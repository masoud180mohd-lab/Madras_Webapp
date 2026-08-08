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

from ..academic import get_active_mwaka
from ..models import Mwanafunzi, Hudhurio, Tangazo, Mwalimu, Darasa, Somo, Nyenzo, Mtihani, Matokeo, RekodiHifdhu, PandeMurajaa, AinaMalipo, Malipo, MsetoMtihani, MwakaWaMasomo
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
from ..audit import andika_ukaguzi_malipo
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

from .helpers import link_callback, paginate_items

@login_required(login_url='ingia')
@ruhusa_capability(CAP_FEES)
def ukurasa_malipo(request):
    wanafunzi = Mwanafunzi.objects.active().select_related('darasa').order_by('jina_kamili')
    active_mwaka = get_active_mwaka()
    mwaka_filter = request.GET.get('mwaka') or (
        str(active_mwaka.id) if active_mwaka else 'yote'
    )
    aina_qs = AinaMalipo.objects.select_related('mwaka')
    if mwaka_filter == 'bila':
        aina_qs = aina_qs.filter(mwaka__isnull=True)
    elif mwaka_filter != 'yote' and str(mwaka_filter).isdigit():
        # Mwaka teule + ada za zamani bila mwaka (mpaka zisasishwe)
        aina_qs = aina_qs.filter(
            Q(mwaka_id=int(mwaka_filter)) | Q(mwaka__isnull=True)
        )
    aina_za_malipo = aina_qs.order_by('-mwaka__mwaka_kuanzia', 'mwezi', 'jina')

    # 1. Pata Vichujio kutoka kwenye URL
    neno_la_kutafuta = request.GET.get('q', '')
    aina_id = request.GET.get('aina', '')
    hali_teule = request.GET.get('hali', 'wote') # KICHUJIO KIPYA CHA DENI
    darasa_filter = request.GET.get('darasa', '')

    if aina_id:
        aina_teule = get_object_or_404(AinaMalipo.objects.select_related('mwaka'), id=aina_id)
    else:
        aina_teule = aina_za_malipo.first()

    if neno_la_kutafuta:
        wanafunzi = wanafunzi.filter(
            Q(jina_kamili__icontains=neno_la_kutafuta) |
            Q(namba_ya_usajili__icontains=neno_la_kutafuta)
        )
    if darasa_filter:
        wanafunzi = wanafunzi.filter(darasa_id=darasa_filter)

    jumla_iliyokusanywa = 0
    idadi_waliolipa = 0
    taarifa_wanafunzi = []

    if aina_teule:
        paid_agg = Malipo.objects.filter(aina_ya_malipo=aina_teule).aggregate(
            jumla=Coalesce(Sum('kiasi_kilicholipwa'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
            walio=Count('mwanafunzi', distinct=True),
        )
        jumla_iliyokusanywa = paid_agg['jumla'] or 0
        idadi_waliolipa = paid_agg['walio'] or 0

        wanafunzi = wanafunzi.annotate(
            jumla_yake=Coalesce(
                Sum(
                    'malipo_yote__kiasi_kilicholipwa',
                    filter=Q(malipo_yote__aina_ya_malipo=aina_teule),
                ),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )

        kinachotakiwa = aina_teule.kiasi_kinachotakiwa
        for m in wanafunzi:
            jumla_yake = m.jumla_yake or 0
            deni = kinachotakiwa - jumla_yake

            if deni <= 0:
                hali = 'Amemaliza'
            elif jumla_yake > 0:
                hali = 'Nusu'
            else:
                hali = 'Hajalipa'

            if hali_teule == 'wanaodaiwa' and hali == 'Amemaliza':
                continue
            if hali_teule == 'waliokamilisha' and hali != 'Amemaliza':
                continue

            taarifa_wanafunzi.append({
                'mwanafunzi': m,
                'jumla_yake': jumla_yake,
                'deni': deni,
                'hali': hali
            })

    page_obj, pagination_query = paginate_items(request, taarifa_wanafunzi, per_page=20)
    madarasa = Darasa.objects.all().order_by('jina')

    context = {
        'aina_za_malipo': aina_za_malipo,
        'aina_teule': aina_teule,
        'jumla_iliyokusanywa': jumla_iliyokusanywa,
        'idadi_waliolipa': idadi_waliolipa,
        'taarifa_wanafunzi': page_obj,
        'page_obj': page_obj,
        'pagination_query': pagination_query,
        'madarasa': madarasa,
        'miaka': MwakaWaMasomo.objects.all().order_by('-mwaka_kuanzia'),
        'mwaka_filter': mwaka_filter,
        'mwaka_hai': active_mwaka,
        'neno_la_kutafuta': neno_la_kutafuta,
        'hali_teule': hali_teule,
        'darasa_filter': darasa_filter,
        'anaweza_weka_malipo': user_has_capability(request.user, CAP_FEES) and user_has_app_permission(request.user, 'usimamizi.add_malipo'),
    }
    return render(request, 'usimamizi/malipo.html', context)

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.add_malipo')
def weka_malipo(request, mwanafunzi_id, aina_id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    aina_ya_malipo = get_object_or_404(AinaMalipo, id=aina_id)
    mwalimu = linked_mwalimu_or_none(request.user)

    jumla_yake = (
        Malipo.objects.filter(mwanafunzi=mwanafunzi, aina_ya_malipo=aina_ya_malipo)
        .aggregate(
            jumla=Coalesce(
                Sum('kiasi_kilicholipwa'),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )['jumla']
        or 0
    )
    deni = aina_ya_malipo.kiasi_kinachotakiwa - jumla_yake

    if request.method == 'POST':
        form = MalipoForm(request.POST, max_kiasi=deni if deni > 0 else None)
        if form.is_valid():
            malipo = Malipo.objects.create(
                mwanafunzi=mwanafunzi,
                aina_ya_malipo=aina_ya_malipo,
                kiasi_kilicholipwa=form.cleaned_data['kiasi'],
                njia_ya_malipo=form.cleaned_data['njia'],
                mpokeaji=mwalimu,
                iliyorekodiwa_na=request.user,
                maelezo_ya_ziada=form.cleaned_data.get('maelezo') or None,
            )
            andika_ukaguzi_malipo(user=request.user, malipo=malipo)
            messages.success(
                request,
                f"✅ Malipo ya Tsh {form.cleaned_data['kiasi']}/= kutoka kwa {mwanafunzi.jina_kamili} yamepokelewa!",
            )
            return redirect(f"{reverse('malipo')}?aina={aina_id}")
        for field_errors in form.errors.values():
            for err in field_errors:
                messages.error(request, err)
    else:
        form = MalipoForm(max_kiasi=deni if deni > 0 else None)

    context = {
        'mwanafunzi': mwanafunzi,
        'aina_ya_malipo': aina_ya_malipo,
        'deni': deni,
        'jumla_yake': jumla_yake,
        'form': form,
    }
    return render(request, 'usimamizi/weka_malipo.html', context)

@login_required(login_url='ingia')
@ruhusa_capability(CAP_FEES)
def pakua_risiti(request, malipo_id):
    malipo = get_object_or_404(
        Malipo.objects.select_related('mwanafunzi', 'aina_ya_malipo', 'mpokeaji'),
        id=malipo_id,
    )
    mwanafunzi = malipo.mwanafunzi
    aina = malipo.aina_ya_malipo

    # Piga hesabu ya deni lililobaki baada ya malipo haya
    jumla_yake = (
        Malipo.objects.filter(mwanafunzi=mwanafunzi, aina_ya_malipo=aina)
        .aggregate(
            jumla=Coalesce(
                Sum('kiasi_kilicholipwa'),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )['jumla']
        or 0
    )
    deni_lililobaki = aina.kiasi_kinachotakiwa - jumla_yake

    context = {
        'malipo': malipo,
        'deni_lililobaki': deni_lililobaki,
        'wakati_huu':  localtime(timezone.now())
    }

    template = get_template('usimamizi/pdf_risiti.html')
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    jina_la_faili = f"Risiti_{mwanafunzi.namba_ya_usajili}_{malipo.id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{jina_la_faili}"'

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse('Kumetokea hitilafu katika kutengeneza Risiti', status=500)
    return response

