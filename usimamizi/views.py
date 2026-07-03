import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.timezone import localtime

from .models import Mwanafunzi, Hudhurio, Tangazo, Mwalimu, Darasa, Somo, Nyenzo, Mtihani, Matokeo, RekodiHifdhu, PandeMurajaa, AinaMalipo, Malipo, MsetoMtihani
from .forms import NyenzoForm, MtihaniForm, MsetoMtihaniForm
from .utils import hesabu_daraja, jenga_ripoti_jumla

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

        for mwanafunzi in wanafunzi:
            yupo = request.POST.get(f'yupo_{mwanafunzi.id}') == 'on'
            sababu = request.POST.get(f'sababu_{mwanafunzi.id}', '')
            Hudhurio.objects.create(
                mwanafunzi=mwanafunzi,
                yupo=yupo,
                sababu_kama_hayupo=sababu,
                aina_ya_rekodi='Kawaida',
                tarehe=leo
            )
        messages.success(request, f'✅ Mahudhurio ya {darasa.jina} yamehifadhiwa kikamilifu!')
        return redirect('wanafunzi_darasa', darasa_id=darasa.id)

    # Tumeongeza 'tayari_yapo' iende kwenye HTML
    context = {'darasa': darasa, 'wanafunzi': wanafunzi, 'leo': leo, 'tayari_yapo': tayari_yapo}
    return render(request, 'usimamizi/mahudhurio_darasa.html', context)

@login_required(login_url='ingia')
def orodha_wanafunzi(request):
    neno_la_kutafuta = request.GET.get('q', '')
    jinsia_filter = request.GET.get('jinsia', '')
    wanafunzi = Mwanafunzi.objects.all().order_by('-id')
    if neno_la_kutafuta:
        wanafunzi = wanafunzi.filter(Q(jina_kamili__icontains=neno_la_kutafuta) | Q(namba_ya_usajili__icontains=neno_la_kutafuta))
    if jinsia_filter:
        wanafunzi = wanafunzi.filter(jinsia=jinsia_filter)

    context = {
        'wanafunzi': wanafunzi,
        'jumla': wanafunzi.count(),
        'wavulana': wanafunzi.filter(jinsia='ME').count(),
        'wasichana': wanafunzi.filter(jinsia='KE').count(),
        'neno_la_kutafuta': neno_la_kutafuta,
        'jinsia_filter': jinsia_filter
    }
    return render(request, 'usimamizi/orodha_wanafunzi.html', context)

@login_required(login_url='ingia')
def hariri_mwanafunzi(request, id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=id)
    if request.method == 'POST':
        mwanafunzi.jina_kamili = request.POST.get('jina')

        # Tunaruhusu ihifadhi Namba ya Usajili kama mtu ataiweka kwa mkono, kama sivyo inabaki na ile ile
        namba = request.POST.get('namba_usajili')
        if namba:
            mwanafunzi.namba_ya_usajili = namba

        mwanafunzi.juzuu_aliyohifadhi = request.POST.get('juzuu')
        mwanafunzi.mahala_anapoishi = request.POST.get('mahala')
        mwanafunzi.jina_la_mzazi = request.POST.get('mzazi')
        mwanafunzi.namba_ya_simu_mzazi = request.POST.get('simu')

        # TUNAPOKEA TAREHE YA KUZALIWA BADALA YA UMRI WA KAWAIDA
        tarehe = request.POST.get('tarehe_kuzaliwa')
        if tarehe:
            mwanafunzi.tarehe_ya_kuzaliwa = tarehe

        mwanafunzi.save()
        messages.success(request, f'✅ Taarifa za {mwanafunzi.jina_kamili} zimesasishwa!')
        return redirect('orodha_wanafunzi')
    return render(request, 'usimamizi/hariri_mwanafunzi.html', {'mwanafunzi': mwanafunzi})

@login_required(login_url='ingia')
def orodha_walimu(request):
    walimu = Mwalimu.objects.all()
    return render(request, 'usimamizi/orodha_walimu.html', {'walimu': walimu})

@login_required(login_url='ingia')
def orodha_madarasa(request):
    madarasa = Darasa.objects.all()
    return render(request, 'usimamizi/orodha_madarasa.html', {'madarasa': madarasa})

@login_required(login_url='ingia')
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
    ).order_by('-idadi_ya_utoro')

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
    ).order_by('-idadi_ya_utoro')

    # 4. Rudisha data kwenye ukurasa wa HTML
    return render(request, 'usimamizi/ripoti_watoro.html', {
        'watoro_chuoni': watoro_chuoni,
        'watoro_darsa': watoro_darsa,
        'kuanzia_tarehe': jumamosi_iliyopita
    })

@login_required(login_url='ingia')
def orodha_masomo(request):
    masomo = Somo.objects.all()
    return render(request, 'usimamizi/orodha_masomo.html', {'masomo': masomo})

@login_required(login_url='ingia')
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
def wanafunzi_hifdhu(request, somo_id):
    somo = get_object_or_404(Somo, id=somo_id)
    wanafunzi = Mwanafunzi.objects.filter(programu_ya_usiku=somo).order_by('jina_kamili')
    return render(request, 'usimamizi/wanafunzi_hifdhu.html', {'somo': somo, 'wanafunzi': wanafunzi})

@login_required(login_url='ingia')
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

        for mwanafunzi in wanafunzi:
            yupo = request.POST.get(f'yupo_{mwanafunzi.id}') == 'on'
            sababu = request.POST.get(f'sababu_{mwanafunzi.id}', '')
            Hudhurio.objects.create(mwanafunzi=mwanafunzi, yupo=yupo, sababu_kama_hayupo=sababu, aina_ya_rekodi='Hifdhu', tarehe=leo)
        messages.success(request, f'✅ Mahudhurio ya Usiku ({somo.jina}) yamehifadhiwa!')
        return redirect('orodha_masomo')

    return render(request, 'usimamizi/mahudhurio_hifdhu.html', {'wanafunzi': wanafunzi, 'leo': leo, 'somo': somo, 'tayari_yapo': tayari_yapo})

@login_required(login_url='ingia')
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
def weka_maksi(request, mtihani_id):
    mtihani = get_object_or_404(Mtihani, id=mtihani_id)
    somo = mtihani.somo

    if somo.darasa:
        wanafunzi = Mwanafunzi.objects.filter(darasa=somo.darasa).order_by('jina_kamili')
    else:
        wanafunzi = Mwanafunzi.objects.all().order_by('jina_kamili')
    if request.method == 'POST':
        for mwanafunzi in wanafunzi:
            maksi_value = request.POST.get(f'maksi_{mwanafunzi.id}')
            if maksi_value:
                Matokeo.objects.update_or_create(
                    mwanafunzi=mwanafunzi,
                    mtihani=mtihani,
                    defaults={'maksi': float(maksi_value)}
                )
        messages.success(request, f'✅ Maksi za mtihani "{mtihani.jina_la_mtihani}" zimehifadhiwa!')
        return redirect('somo_detail', somo_id=somo.id)

    # Tafuta maksi zilizopo ili zi-populate kwenye fomu moja kwa moja
    for mwanafunzi in wanafunzi:
        matokeo = Matokeo.objects.filter(mwanafunzi=mwanafunzi, mtihani=mtihani).first()
        mwanafunzi.maksi_yake = matokeo.maksi if matokeo else ""

    return render(request, 'usimamizi/weka_maksi.html', {
        'mtihani': mtihani,
        'somo': somo,
        'wanafunzi': wanafunzi
    })

@login_required(login_url='ingia')
def mwanafunzi_profile(request, mwanafunzi_id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    return render(request, 'usimamizi/mwanafunzi_profile.html', {'mwanafunzi': mwanafunzi})

@login_required(login_url='ingia')
def rekodi_sabaq(request, mwanafunzi_id, aina):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    mwalimu = get_object_or_404(Mwalimu, user=request.user)

    darasa = mwanafunzi.darasa if aina == 'Darasa' else None
    somo = mwanafunzi.programu_ya_usiku if aina == 'Usiku' else None

    if request.method == 'POST':
        rekodi = RekodiHifdhu.objects.create(
            mwanafunzi=mwanafunzi,
            somo=somo,
            darasa=darasa,
            aina_ya_rekodi=aina,
            mwalimu=mwalimu,
            sabaq_sura=request.POST.get('sabaq_sura'),
            sabaq_aya_kuanzia=request.POST.get('sabaq_aya_kuanzia') or None,
            sabaq_aya_kuishia=request.POST.get('sabaq_aya_kuishia') or None,
            sabaq_hali=request.POST.get('sabaq_hali'),
            maoni_ya_mwalimu=request.POST.get('maoni')
        )

        mapande_sura = request.POST.getlist('pande_sura[]')
        mapande_kuanzia = request.POST.getlist('pande_aya_kuanzia[]')
        mapande_kuishia = request.POST.getlist('pande_aya_kuishia[]')
        mapande_hali = request.POST.getlist('pande_hali[]')

        for i in range(len(mapande_sura)):
            if mapande_sura[i]:
                PandeMurajaa.objects.create(
                    rekodi=rekodi, sura=mapande_sura[i],
                    aya_kuanzia=mapande_kuanzia[i] or None, aya_kuishia=mapande_kuishia[i] or None,
                    hali=mapande_hali[i]
                )

        messages.success(request, f'✅ Tathmini ya {aina} imehifadhiwa kikamilifu!')
        if aina == 'Darasa':
            return redirect('wanafunzi_darasa', darasa_id=darasa.id)
        else:
            return redirect('wanafunzi_hifdhu', somo_id=somo.id)

    return render(request, 'usimamizi/rekodi_hifdhu.html', {'mwanafunzi': mwanafunzi, 'aina': aina, 'somo': somo, 'darasa': darasa})

# ==========================================
# RIPOTI RASMI YA MWANAFUNZI
# ==========================================

@login_required(login_url='ingia')
def ripoti_mwanafunzi(request, mwanafunzi_id, aina):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)

    sabaq = RekodiHifdhu.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi=aina).order_by('-tarehe')
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

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Samahani, kumetokea hitilafu katika kutengeneza PDF', status=500)
    return response

@login_required(login_url='ingia')
def pakua_pdf_sabaq(request, mwanafunzi_id, aina, muda):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    sabaq = RekodiHifdhu.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi=aina).order_by('-tarehe')

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

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Hitilafu ilitokea', status=500)
    return response

@login_required(login_url='ingia')
def ukurasa_malipo(request):
    wanafunzi = Mwanafunzi.objects.all().order_by('jina_kamili')
    aina_za_malipo = AinaMalipo.objects.all().order_by('-tarehe_ya_kuanzishwa')

    # 1. Pata Vichujio kutoka kwenye URL
    neno_la_kutafuta = request.GET.get('q', '')
    aina_id = request.GET.get('aina', '')
    hali_teule = request.GET.get('hali', 'wote') # KICHUJIO KIPYA CHA DENI

    if aina_id:
        aina_teule = get_object_or_404(AinaMalipo, id=aina_id)
    else:
        aina_teule = aina_za_malipo.first()

    if neno_la_kutafuta:
        wanafunzi = wanafunzi.filter(
            Q(jina_kamili__icontains=neno_la_kutafuta) |
            Q(namba_ya_usajili__icontains=neno_la_kutafuta)
        )

    jumla_iliyokusanywa = 0
    idadi_waliolipa = 0
    taarifa_wanafunzi = []

    if aina_teule:
        malipo_yote = Malipo.objects.filter(aina_ya_malipo=aina_teule)
        jumla_iliyokusanywa = sum([p.kiasi_kilicholipwa for p in malipo_yote])
        idadi_waliolipa = malipo_yote.values('mwanafunzi').distinct().count()

        for m in wanafunzi:
            malipo_yake = malipo_yote.filter(mwanafunzi=m)
            jumla_yake = sum([p.kiasi_kilicholipwa for p in malipo_yake])
            deni = aina_teule.kiasi_kinachotakiwa - jumla_yake

            if deni <= 0:
                hali = 'Amemaliza'
            elif jumla_yake > 0:
                hali = 'Nusu'
            else:
                hali = 'Hajalipa'

            # AKILI MPYA YA KUCHUJA WANAODAIWA NA WALIOKAMILISHA
            if hali_teule == 'wanaodaiwa' and hali == 'Amemaliza':
                continue # Ruka huyu, tunataka wanaodaiwa tu
            if hali_teule == 'waliokamilisha' and hali != 'Amemaliza':
                continue # Ruka huyu, tunataka waliomaliza tu

            taarifa_wanafunzi.append({
                'mwanafunzi': m,
                'jumla_yake': jumla_yake,
                'deni': deni,
                'hali': hali
            })

    context = {
        'aina_za_malipo': aina_za_malipo,
        'aina_teule': aina_teule,
        'jumla_iliyokusanywa': jumla_iliyokusanywa,
        'idadi_waliolipa': idadi_waliolipa,
        'taarifa_wanafunzi': taarifa_wanafunzi,
        'neno_la_kutafuta': neno_la_kutafuta,
        'hali_teule': hali_teule, # Tunapeleka Hali kwenye HTML
    }
    return render(request, 'usimamizi/malipo.html', context)

@login_required(login_url='ingia')
def weka_malipo(request, mwanafunzi_id, aina_id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    aina_ya_malipo = get_object_or_404(AinaMalipo, id=aina_id)
    mwalimu = get_object_or_404(Mwalimu, user=request.user)

    malipo_yake = Malipo.objects.filter(mwanafunzi=mwanafunzi, aina_ya_malipo=aina_ya_malipo)
    jumla_yake = sum([p.kiasi_kilicholipwa for p in malipo_yake])
    deni = aina_ya_malipo.kiasi_kinachotakiwa - jumla_yake

    if request.method == 'POST':
        kiasi = request.POST.get('kiasi')
        njia = request.POST.get('njia')
        maelezo = request.POST.get('maelezo')

        if kiasi and float(kiasi) > 0:
            Malipo.objects.create(
                mwanafunzi=mwanafunzi,
                aina_ya_malipo=aina_ya_malipo,
                kiasi_kilicholipwa=kiasi,
                njia_ya_malipo=njia,
                mpokeaji=mwalimu,
                maelezo_ya_ziada=maelezo
            )
            messages.success(request, f'✅ Malipo ya Tsh {kiasi}/= kutoka kwa {mwanafunzi.jina_kamili} yamepokelewa!')
            # Turudi kwenye ukurasa mkuu huku tukikumbuka Aina iliyokuwa inatazamwa
            return redirect(f"/madrasa/malipo/?aina={aina_id}")

    context = {
        'mwanafunzi': mwanafunzi,
        'aina_ya_malipo': aina_ya_malipo,
        'deni': deni,
        'jumla_yake': jumla_yake
    }
    return render(request, 'usimamizi/weka_malipo.html', context)

@login_required(login_url='ingia')
def pakua_risiti(request, malipo_id):
    malipo = get_object_or_404(Malipo, id=malipo_id)
    mwanafunzi = malipo.mwanafunzi
    aina = malipo.aina_ya_malipo

    # Piga hesabu ya deni lililobaki baada ya malipo haya
    malipo_yote = Malipo.objects.filter(mwanafunzi=mwanafunzi, aina_ya_malipo=aina)
    jumla_yake = sum([p.kiasi_kilicholipwa for p in malipo_yote])
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

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Kumetokea hitilafu katika kutengeneza Risiti', status=500)
    return response

    # ==========================================
# RIPOTI YA MTIHANI (MATOKEO YA DARASA LAKO)
# ==========================================
@login_required(login_url='ingia')
def tazama_matokeo(request, mtihani_id):
    mtihani = get_object_or_404(Mtihani, id=mtihani_id)
    somo = mtihani.somo

    # Tunavuta matokeo na kupanga kuanzia Maksi kubwa kwenda ndogo (Ranking)
    matokeo_yote = Matokeo.objects.filter(mtihani=mtihani).order_by('-maksi')

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
def pakua_pdf_matokeo(request, mtihani_id):
    mtihani = get_object_or_404(Mtihani, id=mtihani_id)
    somo = mtihani.somo
    matokeo_yote = Matokeo.objects.filter(mtihani=mtihani).order_by('-maksi')

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

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Kumetokea hitilafu katika kutengeneza PDF ya matokeo', status=500)
    return response


# ==========================================
# MSETO WA MITIHANI NA RIPOTI YA JUMLA
# ==========================================

@login_required(login_url='ingia')
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
def pakua_pdf_matokeo_jumla(request, darasa_id, mseto_id):
    darasa = get_object_or_404(Darasa, id=darasa_id)
    mseto = get_object_or_404(MsetoMtihani, id=mseto_id, darasa=darasa)
    ripoti = jenga_ripoti_jumla(mseto)

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

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Kumetokea hitilafu katika kutengeneza PDF ya matokeo ya jumla', status=500)
    return response


@login_required(login_url='ingia')
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
