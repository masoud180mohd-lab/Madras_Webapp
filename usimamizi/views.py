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

from .models import Mwanafunzi, Hudhurio, Tangazo, Mwalimu, Darasa, Somo, Nyenzo, Mtihani, Matokeo, RekodiHifdhu, PandeMurajaa, AinaMalipo, Malipo, MsetoMtihani
from .forms import (
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
from .utils import hesabu_daraja, jenga_ripoti_jumla
from .permissions import (
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


def link_callback(uri, rel):
    parsed_uri = urlparse(uri)
    path = parsed_uri.path or uri

    if path.startswith(settings.MEDIA_URL):
        media_path = os.path.join(settings.MEDIA_ROOT, path.replace(settings.MEDIA_URL, "", 1))
        if os.path.isfile(media_path):
            return media_path

    static_url = settings.STATIC_URL
    candidates = [static_url]
    if static_url.startswith("/"):
        candidates.append(static_url.lstrip("/"))
    else:
        candidates.append("/" + static_url)

    for candidate in candidates:
        if path.startswith(candidate):
            relative_path = path.replace(candidate, "", 1)
            static_path = finders.find(relative_path)
            if static_path:
                return static_path
            if settings.STATIC_ROOT:
                return os.path.join(settings.STATIC_ROOT, relative_path)

    static_path = finders.find(path.lstrip("/"))
    if static_path:
        return static_path

    return uri

def paginate_items(request, items, per_page=20):
    paginator = Paginator(items, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))
    query_params = request.GET.copy()
    query_params.pop('page', None)
    return page_obj, query_params.urlencode()


def ingia(request):
    if request.method == 'POST':
        jina = request.POST.get('username')
        siri = request.POST.get('password')
        user = authenticate(request, username=jina, password=siri)
        if user is not None:
            login(request, user)
            return redirect('mwanzo')
        else:
            messages.error(request, '❌ Jina au Password uliyoweka si sahihi!')
    return render(request, 'usimamizi/ingia.html')

def toka(request):
    logout(request)
    return redirect('ingia')

@login_required(login_url='ingia')
def ukurasa_wa_mwanzo(request):
    matangazo = Tangazo.objects.all().order_by('-tarehe_iliyotolewa')[:5]
    return render(request, 'usimamizi/mwanzo.html', {'matangazo': matangazo})

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.add_hudhurio')
def mahudhurio_darasa(request, darasa_id):
    darasa = get_object_or_404(Darasa, id=darasa_id)
    wanafunzi = Mwanafunzi.objects.filter(darasa=darasa).order_by('jina_kamili')
    leo = date.today()

    # KODI MPYA: Cheki kama mahudhurio ya leo yapo tayari kwa darasa hili
    tayari_yapo = Hudhurio.objects.filter(
        mwanafunzi__darasa=darasa,
        tarehe=leo,
        aina_ya_rekodi='Kawaida'
    ).exists()

    if request.method == 'POST':
        # Kama yapo tayari, zuia isihifadhi tena
        if tayari_yapo:
            messages.error(request, '❌ Mahudhurio ya siku ya leo tayari yasharikodiwa!')
            return redirect('mahudhurio_darasa', darasa_id=darasa.id)

        rows = build_hudhurio_rows(
            wanafunzi, request.POST, aina_ya_rekodi='Kawaida', tarehe=leo
        )
        Hudhurio.objects.bulk_create(rows)
        messages.success(request, f'✅ Mahudhurio ya {darasa.jina} yamehifadhiwa kikamilifu!')
        return redirect('wanafunzi_darasa', darasa_id=darasa.id)

    # Tumeongeza 'tayari_yapo' iende kwenye HTML
    context = {'darasa': darasa, 'wanafunzi': wanafunzi, 'leo': leo, 'tayari_yapo': tayari_yapo}
    return render(request, 'usimamizi/mahudhurio_darasa.html', context)

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_STUDENTS)
def orodha_wanafunzi(request):
    neno_la_kutafuta = request.GET.get('q', '')
    jinsia_filter = request.GET.get('jinsia', '')
    darasa_filter = request.GET.get('darasa', '')
    wanafunzi = Mwanafunzi.objects.all().order_by('-id')
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
    wanafunzi = Mwanafunzi.objects.filter(darasa=darasa)

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
    watoro_chuoni = Mwanafunzi.objects.filter(
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
    watoro_darsa = Mwanafunzi.objects.filter(
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

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_DIRECTORY, CAP_EXAMS, CAP_MATERIALS)
def orodha_masomo(request):
    masomo = Somo.objects.select_related('mwalimu__user', 'darasa').all()
    return render(request, 'usimamizi/orodha_masomo.html', {'masomo': masomo})

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_DIRECTORY, CAP_EXAMS, CAP_MATERIALS)
def somo_detail(request, somo_id):
    somo = get_object_or_404(Somo, id=somo_id)
    if somo.ni_la_hifdhu:
        idadi = Mwanafunzi.objects.filter(programu_ya_usiku=somo).count()
        return render(request, 'usimamizi/somo_hifdhu.html', {'somo': somo, 'idadi': idadi})
    else:
        nyenzo = Nyenzo.objects.filter(somo=somo).order_by('-tarehe_iliyowekwa')
        mitihani = Mtihani.objects.filter(somo=somo).order_by('-tarehe')
        return render(request, 'usimamizi/somo_kawaida.html', {'somo': somo, 'nyenzo': nyenzo, 'mitihani': mitihani})

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_STUDENTS, CAP_SABAQ, CAP_ATTENDANCE)
def wanafunzi_hifdhu(request, somo_id):
    somo = get_object_or_404(Somo, id=somo_id)
    wanafunzi = Mwanafunzi.objects.filter(programu_ya_usiku=somo).order_by('jina_kamili')
    return render(request, 'usimamizi/wanafunzi_hifdhu.html', {'somo': somo, 'wanafunzi': wanafunzi})

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.add_hudhurio')
def chukua_mahudhurio_hifdhu(request, somo_id):
    somo = get_object_or_404(Somo, id=somo_id)
    wanafunzi = Mwanafunzi.objects.filter(programu_ya_usiku=somo).order_by('jina_kamili')
    leo = date.today()

    # KODI MPYA: Cheki kama mahudhurio ya leo yapo tayari kwa somo hili
    tayari_yapo = Hudhurio.objects.filter(
        mwanafunzi__programu_ya_usiku=somo,
        tarehe=leo,
        aina_ya_rekodi='Hifdhu'
    ).exists()

    if request.method == 'POST':
        # Kama yapo tayari, zuia
        if tayari_yapo:
            messages.error(request, '❌ Mahudhurio ya siku ya leo tayari yasharikodiwa!')
            return redirect('chukua_mahudhurio_hifdhu', somo_id=somo.id)

        rows = build_hudhurio_rows(
            wanafunzi, request.POST, aina_ya_rekodi='Hifdhu', tarehe=leo
        )
        Hudhurio.objects.bulk_create(rows)
        messages.success(request, f'✅ Mahudhurio ya Usiku ({somo.jina}) yamehifadhiwa!')
        return redirect('orodha_masomo')

    return render(request, 'usimamizi/mahudhurio_hifdhu.html', {'wanafunzi': wanafunzi, 'leo': leo, 'somo': somo, 'tayari_yapo': tayari_yapo})

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.add_nyenzo')
def pakia_nyenzo(request, somo_id):
    somo = get_object_or_404(Somo, id=somo_id)
    if request.method == 'POST':
        form = NyenzoForm(request.POST, request.FILES)
        if form.is_valid():
            nyenzo = form.save(commit=False)
            nyenzo.somo = somo
            nyenzo.save()
            messages.success(request, f"Nyenzo imepakiwa kikamilifu kwenye somo la {somo.jina}!")
            return redirect('somo_detail', somo_id=somo.id)
    else:
        form = NyenzoForm()
    return render(request, 'usimamizi/fomu_somo.html', {'form': form, 'somo': somo, 'aina': 'Nyenzo'})

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.add_mtihani')
def ongeza_mtihani(request, somo_id):
    somo = get_object_or_404(Somo, id=somo_id)
    if request.method == 'POST':
        form = MtihaniForm(request.POST, darasa=somo.darasa)
        if form.is_valid():
            mtihani = form.save(commit=False)
            mtihani.somo = somo
            mtihani.save()
            messages.success(request, f"Mtihani umesajiliwa kikamilifu kwenye {somo.jina}!")
            return redirect('somo_detail', somo_id=somo.id)
    else:
        form = MtihaniForm(darasa=somo.darasa)
    return render(request, 'usimamizi/fomu_somo.html', {'form': form, 'somo': somo, 'aina': 'Mtihani'})

# ==========================================
# HII NDIO FUNCTION MPYA YA MAKSI
# ==========================================
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
@ruhusa_capability(CAP_VIEW_STUDENTS)
def mwanafunzi_profile(request, mwanafunzi_id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    tab_teule = request.GET.get('tab', 'muhtasari')
    mahudhurio_kawaida = Hudhurio.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi='Kawaida').order_by('-tarehe')
    mahudhurio_hifdhu = Hudhurio.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi='Hifdhu').order_by('-tarehe')
    malipo_yote = mwanafunzi.malipo_yote.select_related('aina_ya_malipo').order_by('-tarehe_ya_malipo')
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

    return render(request, 'usimamizi/mwanafunzi_profile.html', {
        'mwanafunzi': mwanafunzi,
        'tab_teule': tab_teule,
        'mahudhurio_kawaida': mahudhurio_kawaida,
        'mahudhurio_hifdhu': mahudhurio_hifdhu,
        'malipo_yote': malipo_yote,
        'sabaq_darasa': sabaq_darasa,
        'sabaq_usiku': sabaq_usiku,
        'jumla_malipo': jumla_malipo,
    })

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.add_rekodihifdhu')
def rekodi_sabaq(request, mwanafunzi_id, aina):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    mwalimu = require_linked_mwalimu(request)
    if mwalimu is None:
        return redirect('mwanzo')

    darasa = mwanafunzi.darasa if aina == 'Darasa' else None
    somo = mwanafunzi.programu_ya_usiku if aina == 'Usiku' else None

    if request.method == 'POST':
        form = SabaqRekodiForm(request.POST)
        mapande_rows, mapande_errors = parse_mapande_from_post(request.POST)
        if not form.is_valid() or mapande_errors:
            for field_errors in form.errors.values():
                for err in field_errors:
                    messages.error(request, err)
            for err in mapande_errors:
                messages.error(request, err)
            return render(
                request,
                'usimamizi/rekodi_hifdhu.html',
                {'mwanafunzi': mwanafunzi, 'aina': aina, 'somo': somo, 'darasa': darasa, 'form': form},
            )

        cleaned = form.cleaned_data
        rekodi = RekodiHifdhu.objects.create(
            mwanafunzi=mwanafunzi,
            somo=somo,
            darasa=darasa,
            aina_ya_rekodi=aina,
            mwalimu=mwalimu,
            sabaq_sura=cleaned.get('sabaq_sura') or None,
            sabaq_aya_kuanzia=cleaned.get('sabaq_aya_kuanzia'),
            sabaq_aya_kuishia=cleaned.get('sabaq_aya_kuishia'),
            sabaq_hali=cleaned.get('sabaq_hali') or None,
            maoni_ya_mwalimu=cleaned.get('maoni') or None,
        )

        PandeMurajaa.objects.bulk_create(
            [
                PandeMurajaa(
                    rekodi=rekodi,
                    sura=row['sura'],
                    aya_kuanzia=row['aya_kuanzia'],
                    aya_kuishia=row['aya_kuishia'],
                    hali=row['hali'],
                )
                for row in mapande_rows
            ]
        )

        messages.success(request, f'✅ Tathmini ya {aina} imehifadhiwa kikamilifu!')
        if aina == 'Darasa':
            return redirect('wanafunzi_darasa', darasa_id=darasa.id)
        else:
            return redirect('wanafunzi_hifdhu', somo_id=somo.id)

    return render(
        request,
        'usimamizi/rekodi_hifdhu.html',
        {
            'mwanafunzi': mwanafunzi,
            'aina': aina,
            'somo': somo,
            'darasa': darasa,
            'form': SabaqRekodiForm(),
        },
    )

# ==========================================
# RIPOTI RASMI YA MWANAFUNZI
# ==========================================

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_STUDENTS)
def ripoti_mwanafunzi(request, mwanafunzi_id, aina):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)

    sabaq = (
        RekodiHifdhu.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi=aina)
        .prefetch_related('mapande')
        .order_by('-tarehe')
    )
    aina_hudhurio = 'Kawaida' if aina == 'Darasa' else 'Hifdhu'
    mahudhurio = Hudhurio.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi=aina_hudhurio).order_by('-tarehe')

    muda = request.GET.get('muda', 'wote')
    tab_teule = request.GET.get('tab', 'mahudhurio')
    leo = timezone.now().date()

    if muda == 'wiki':
        tangu = leo - timedelta(days=7)
        mahudhurio = mahudhurio.filter(tarehe__gte=tangu)
        sabaq = sabaq.filter(tarehe__gte=tangu)
    elif muda == 'mwezi_huu':
        mahudhurio = mahudhurio.filter(tarehe__year=leo.year, tarehe__month=leo.month)
        sabaq = sabaq.filter(tarehe__year=leo.year, tarehe__month=leo.month)
    elif muda == 'mwezi_uliopita':
        mwezi_uliopita = leo.month - 1 if leo.month > 1 else 12
        mwaka = leo.year if leo.month > 1 else leo.year - 1
        mahudhurio = mahudhurio.filter(tarehe__year=mwaka, tarehe__month=mwezi_uliopita)
        sabaq = sabaq.filter(tarehe__year=mwaka, tarehe__month=mwezi_uliopita)

    context = {
        'mwanafunzi': mwanafunzi, 'aina': aina,
        'mahudhurio': mahudhurio, 'sabaq': sabaq,
        'muda_teule': muda, 'tab_teule': tab_teule
    }
    return render(request, 'usimamizi/ripoti_mwanafunzi.html', context)

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_STUDENTS, CAP_ATTENDANCE)
def pakua_pdf_mahudhurio(request, mwanafunzi_id, aina, muda):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    aina_hudhurio = 'Kawaida' if aina == 'Darasa' else 'Hifdhu'
    mahudhurio = Hudhurio.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi=aina_hudhurio).order_by('-tarehe')

    leo = timezone.now().date()
    if muda == 'wiki':
        tangu = leo - timedelta(days=7)
        mahudhurio = mahudhurio.filter(tarehe__gte=tangu)
    elif muda == 'mwezi_huu':
        mahudhurio = mahudhurio.filter(tarehe__year=leo.year, tarehe__month=leo.month)
    elif muda == 'mwezi_uliopita':
        mwezi_uliopita = leo.month - 1 if leo.month > 1 else 12
        mwaka = leo.year if leo.month > 1 else leo.year - 1
        mahudhurio = mahudhurio.filter(tarehe__year=mwaka, tarehe__month=mwezi_uliopita)

    muda_wa_sasa = localtime(timezone.now())
    context = {'mwanafunzi': mwanafunzi, 'mahudhurio': mahudhurio, 'aina': aina, 'muda': muda, 'wakati_huu': muda_wa_sasa}

    template = get_template('usimamizi/pdf_mahudhurio.html')
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    jina_la_faili = f"Mahudhurio_{mwanafunzi.namba_ya_usajili}_{muda_wa_sasa.strftime('%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{jina_la_faili}"'

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse('Samahani, kumetokea hitilafu katika kutengeneza PDF', status=500)
    return response

@login_required(login_url='ingia')
@ruhusa_capability(CAP_VIEW_STUDENTS, CAP_SABAQ)
def pakua_pdf_sabaq(request, mwanafunzi_id, aina, muda):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    sabaq = (
        RekodiHifdhu.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi=aina)
        .prefetch_related('mapande')
        .order_by('-tarehe')
    )

    leo = timezone.now().date()
    if muda == 'wiki':
        tangu = leo - timedelta(days=7)
        sabaq = sabaq.filter(tarehe__gte=tangu)
    elif muda == 'mwezi_huu':
        sabaq = sabaq.filter(tarehe__year=leo.year, tarehe__month=leo.month)
    elif muda == 'mwezi_uliopita':
        mwezi_uliopita = leo.month - 1 if leo.month > 1 else 12
        mwaka = leo.year if leo.month > 1 else leo.year - 1
        sabaq = sabaq.filter(tarehe__year=mwaka, tarehe__month=mwezi_uliopita)

    muda_wa_sasa = localtime(timezone.now())
    context = {'mwanafunzi': mwanafunzi, 'sabaq': sabaq, 'aina': aina, 'wakati_huu': muda_wa_sasa}

    template = get_template('usimamizi/pdf_sabaq.html')
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    jina_la_faili = f"Sabaq_{mwanafunzi.namba_ya_usajili}_{muda_wa_sasa.strftime('%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{jina_la_faili}"'

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse('Hitilafu ilitokea', status=500)
    return response

@login_required(login_url='ingia')
@ruhusa_capability(CAP_FEES)
def ukurasa_malipo(request):
    wanafunzi = Mwanafunzi.objects.select_related('darasa').order_by('jina_kamili')
    aina_za_malipo = AinaMalipo.objects.all().order_by('-tarehe_ya_kuanzishwa')

    # 1. Pata Vichujio kutoka kwenye URL
    neno_la_kutafuta = request.GET.get('q', '')
    aina_id = request.GET.get('aina', '')
    hali_teule = request.GET.get('hali', 'wote') # KICHUJIO KIPYA CHA DENI
    darasa_filter = request.GET.get('darasa', '')

    if aina_id:
        aina_teule = get_object_or_404(AinaMalipo, id=aina_id)
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
            Malipo.objects.create(
                mwanafunzi=mwanafunzi,
                aina_ya_malipo=aina_ya_malipo,
                kiasi_kilicholipwa=form.cleaned_data['kiasi'],
                njia_ya_malipo=form.cleaned_data['njia'],
                mpokeaji=mwalimu,
                maelezo_ya_ziada=form.cleaned_data.get('maelezo') or None,
            )
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

    # ==========================================
# RIPOTI YA MTIHANI (MATOKEO YA DARASA LAKO)
# ==========================================
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

    # ==========================================
# KUTENGENEZA PDF YA MATOKEO
# ==========================================
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


# ==========================================
# MSETO WA MITIHANI NA RIPOTI YA JUMLA
# ==========================================

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
