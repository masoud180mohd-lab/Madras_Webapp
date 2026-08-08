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
from django.views.decorators.http import require_POST
from datetime import date, timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.timezone import localtime
from django.urls import reverse

from ..models import (
    Mwanafunzi,
    Hudhurio,
    Tangazo,
    Mwalimu,
    Darasa,
    Somo,
    Nyenzo,
    Mtihani,
    Matokeo,
    RekodiHifdhu,
    RekodiMaendeleoMchana,
    PandeMurajaa,
    AinaMalipo,
    Malipo,
    MsetoMtihani,
)
from ..forms import (
    MwanafunziForm,
    NyenzoForm,
    MtihaniForm,
    MsetoMtihaniForm,
    MalipoForm,
    RekodiSimuMzaziForm,
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
    CAP_PARENT_CONTACT,
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

from .helpers import paginate_items

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_STUDENTS)
def orodha_wanafunzi(request):
    neno_la_kutafuta = request.GET.get('q', '')
    jinsia_filter = request.GET.get('jinsia', '')
    darasa_filter = request.GET.get('darasa', '')
    hali_filter = request.GET.get('hali', 'hai')
    if hali_filter not in ('hai', 'hifadhiwa'):
        hali_filter = 'hai'

    wanafunzi = Mwanafunzi.objects.all().order_by('-id')
    if hali_filter == 'hifadhiwa':
        wanafunzi = wanafunzi.archived()
    else:
        wanafunzi = wanafunzi.active()

    if neno_la_kutafuta:
        wanafunzi = wanafunzi.filter(Q(jina_kamili__icontains=neno_la_kutafuta) | Q(namba_ya_usajili__icontains=neno_la_kutafuta))
    if jinsia_filter:
        wanafunzi = wanafunzi.filter(jinsia=jinsia_filter)
    if darasa_filter:
        wanafunzi = wanafunzi.filter(darasa_id=darasa_filter)

    page_obj, pagination_query = paginate_items(request, wanafunzi, per_page=20)
    madarasa = Darasa.objects.all().order_by('jina')

    context = {
        'wanafunzi': page_obj,
        'page_obj': page_obj,
        'pagination_query': pagination_query,
        'madarasa': madarasa,
        'jumla': wanafunzi.count(),
        'wavulana': wanafunzi.filter(jinsia='ME').count(),
        'wasichana': wanafunzi.filter(jinsia='KE').count(),
        'neno_la_kutafuta': neno_la_kutafuta,
        'jinsia_filter': jinsia_filter,
        'darasa_filter': darasa_filter,
        'hali_filter': hali_filter,
        'anaweza_sajili_mwanafunzi': user_has_capability(request.user, CAP_MANAGE_STUDENTS),
    }
    return render(request, 'usimamizi/orodha_wanafunzi.html', context)

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.add_mwanafunzi')
def sajili_mwanafunzi(request):
    if request.method == 'POST':
        form = MwanafunziForm(request.POST, request.FILES)
        if form.is_valid():
            mwanafunzi = form.save()
            messages.success(request, f'Mwanafunzi {mwanafunzi.jina_kamili} amesajiliwa kikamilifu!')
            return redirect('mwanafunzi_profile', mwanafunzi_id=mwanafunzi.id)
    else:
        form = MwanafunziForm()
    return render(request, 'usimamizi/fomu_mwanafunzi.html', {
        'form': form,
        'kichwa': 'Sajili Mwanafunzi',
        'maelezo': 'Jaza taarifa za msingi na picha ya mwanafunzi.',
        'kitufe': 'Sajili Mwanafunzi',
    })

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.change_mwanafunzi')
def hariri_mwanafunzi(request, id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=id)
    if mwanafunzi.amehifadhiwa:
        messages.error(
            request,
            'Mwanafunzi huyu amehifadhiwa. Rudisha kwenye orodha hai kabla ya kuhariri.',
        )
        return redirect('mwanafunzi_profile', mwanafunzi_id=mwanafunzi.id)
    if request.method == 'POST':
        form = MwanafunziForm(request.POST, request.FILES, instance=mwanafunzi)
        if form.is_valid():
            mwanafunzi = form.save()
            messages.success(request, f'Taarifa za {mwanafunzi.jina_kamili} zimesasishwa!')
            return redirect('mwanafunzi_profile', mwanafunzi_id=mwanafunzi.id)
    else:
        form = MwanafunziForm(instance=mwanafunzi)
    return render(request, 'usimamizi/fomu_mwanafunzi.html', {
        'form': form,
        'mwanafunzi': mwanafunzi,
        'kichwa': 'Hariri Taarifa',
        'maelezo': f'Mwanafunzi: {mwanafunzi.jina_kamili}',
        'kitufe': 'Hifadhi Mabadiliko',
    })

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_DIRECTORY)
def orodha_walimu(request):
    walimu = Mwalimu.objects.select_related('user').all()
    return render(request, 'usimamizi/orodha_walimu.html', {'walimu': walimu})

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_DIRECTORY)
def orodha_madarasa(request):
    madarasa = Darasa.objects.all()
    return render(request, 'usimamizi/orodha_madarasa.html', {'madarasa': madarasa})

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_STUDENTS)
def wanafunzi_darasa(request, darasa_id):
    darasa = get_object_or_404(Darasa, id=darasa_id)
    wanafunzi = Mwanafunzi.objects.active().filter(darasa=darasa)

    jumla = wanafunzi.count()
    wavulana = wanafunzi.filter(jinsia='ME').count()
    wasichana = wanafunzi.filter(jinsia='KE').count()

    return render(request, 'usimamizi/wanafunzi_darasa.html', {
        'darasa': darasa,
        'wanafunzi': wanafunzi,
        'jumla': jumla,
        'wavulana': wavulana,
        'wasichana': wasichana
    })

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_STUDENTS)
def mwanafunzi_profile(request, mwanafunzi_id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    tab_teule = request.GET.get('tab', 'muhtasari')
    mahudhurio_kawaida = Hudhurio.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi='Kawaida').order_by('-tarehe')
    mahudhurio_hifdhu = Hudhurio.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi='Hifdhu').order_by('-tarehe')
    malipo_yote = (
        mwanafunzi.malipo_yote.select_related(
            'aina_ya_malipo', 'mpokeaji', 'iliyorekodiwa_na'
        ).order_by('-tarehe_ya_malipo')
    )
    sabaq_darasa = (
        RekodiHifdhu.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi='Darasa')
        .select_related('somo', 'mwalimu')
        .prefetch_related('mapande')
        .order_by('-tarehe')
    )
    sabaq_usiku = (
        RekodiHifdhu.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi='Usiku')
        .select_related('somo', 'mwalimu')
        .prefetch_related('mapande')
        .order_by('-tarehe')
    )
    jumla_malipo = malipo_yote.aggregate(jumla=Sum('kiasi_kilicholipwa'))['jumla'] or 0
    anaweza_fuata_wazazi = user_has_capability(
        request.user, CAP_PARENT_CONTACT
    )
    rekodi_simu = []
    call_form = None
    if anaweza_fuata_wazazi:
        rekodi_simu = mwanafunzi.rekodi_simu.select_related(
            "iliyorekodiwa_na"
        ).all()[:30]
        call_form = RekodiSimuMzaziForm(mwanafunzi=mwanafunzi)

    maendeleo_mchana = (
        RekodiMaendeleoMchana.objects.filter(mwanafunzi=mwanafunzi)
        .select_related("somo", "mwalimu__user")
        .order_by("-tarehe")[:12]
    )

    return render(request, 'usimamizi/mwanafunzi_profile.html', {
        'mwanafunzi': mwanafunzi,
        'tab_teule': tab_teule,
        'mahudhurio_kawaida': mahudhurio_kawaida,
        'mahudhurio_hifdhu': mahudhurio_hifdhu,
        'malipo_yote': malipo_yote,
        'sabaq_darasa': sabaq_darasa,
        'sabaq_usiku': sabaq_usiku,
        'maendeleo_mchana': maendeleo_mchana,
        'jumla_malipo': jumla_malipo,
        'anaweza_simamia_wanafunzi': user_has_capability(
            request.user, CAP_MANAGE_STUDENTS
        ),
        'anaweza_fuata_wazazi': anaweza_fuata_wazazi,
        'rekodi_simu': rekodi_simu,
        'call_form': call_form,
    })


@login_required(login_url='ingia')
@ruhusa_capability(CAP_MANAGE_STUDENTS)
@require_POST
def hifadhi_mwanafunzi(request, mwanafunzi_id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    if mwanafunzi.amehifadhiwa:
        messages.info(request, f'{mwanafunzi.jina_kamili} tayari amehifadhiwa.')
    else:
        mwanafunzi.archive(sababu=request.POST.get('sababu', ''))
        messages.success(
            request,
            f'{mwanafunzi.jina_kamili} amehifadhiwa. Historia inabaki; haonekani kwenye orodha hai.',
        )
    return redirect('mwanafunzi_profile', mwanafunzi_id=mwanafunzi.id)


@login_required(login_url='ingia')
@ruhusa_capability(CAP_MANAGE_STUDENTS)
@require_POST
def rudisha_mwanafunzi(request, mwanafunzi_id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    if not mwanafunzi.amehifadhiwa:
        messages.info(request, f'{mwanafunzi.jina_kamili} tayari yupo kwenye orodha hai.')
    else:
        mwanafunzi.restore()
        messages.success(
            request,
            f'{mwanafunzi.jina_kamili} amerudishwa kwenye orodha hai.',
        )
    return redirect('mwanafunzi_profile', mwanafunzi_id=mwanafunzi.id)

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_STUDENTS, CAP_ATTENDANCE)
def ripoti_watoro(request):
    """
    Function hii inatafuta watoro kuanzia Jumamosi iliyopita mpaka sasa.
    Hii inahakikisha mwalimu anaona utoro wa wiki nzima ya kazi
    bila kujali anafungua ripoti siku gani.
    """
    leo = timezone.now().date()

    # 1. Piga hesabu ya kurudi nyuma mpaka Jumamosi iliyopita
    # (leo.weekday() ni 0=Jumatatu ... 5=Jumamosi)
    siku_za_kurudi_nyuma = (leo.weekday() - 5) % 7

    # Kama leo ni Jumamosi, rudi nyuma siku 7 ili uanze wiki mpya
    if siku_za_kurudi_nyuma == 0:
        siku_za_kurudi_nyuma = 7

    jumamosi_iliyopita = leo - timedelta(days=siku_za_kurudi_nyuma)

    # 2. WATORO WA CHUONI (Kawaida - Mchana)
    # Tunachuja kwa tarehe kuanzia Jumamosi iliyopita, yupo=False, na aina=Kawaida
    watoro_chuoni = Mwanafunzi.objects.active().filter(
        hudhurio__tarehe__gte=jumamosi_iliyopita,
        hudhurio__yupo=False,
        hudhurio__aina_ya_rekodi='Kawaida'
    ).distinct().annotate(
        idadi_ya_utoro=Count('hudhurio', filter=Q(
            hudhurio__tarehe__gte=jumamosi_iliyopita,
            hudhurio__yupo=False,
            hudhurio__aina_ya_rekodi='Kawaida'
        ))
    ).select_related('darasa', 'programu_ya_usiku').order_by('-idadi_ya_utoro')

    # 3. WATORO WA DARSA (Hifdhu - Usiku)
    # Tunachuja kwa tarehe kuanzia Jumamosi iliyopita, yupo=False, na aina=Hifdhu
    watoro_darsa = Mwanafunzi.objects.active().filter(
        hudhurio__tarehe__gte=jumamosi_iliyopita,
        hudhurio__yupo=False,
        hudhurio__aina_ya_rekodi='Hifdhu'
    ).distinct().annotate(
        idadi_ya_utoro=Count('hudhurio', filter=Q(
            hudhurio__tarehe__gte=jumamosi_iliyopita,
            hudhurio__yupo=False,
            hudhurio__aina_ya_rekodi='Hifdhu'
        ))
    ).select_related('darasa', 'programu_ya_usiku').order_by('-idadi_ya_utoro')

    # 4. Rudisha data kwenye ukurasa wa HTML
    return render(request, 'usimamizi/ripoti_watoro.html', {
        'watoro_chuoni': watoro_chuoni,
        'watoro_darsa': watoro_darsa,
        'kuanzia_tarehe': jumamosi_iliyopita
    })

