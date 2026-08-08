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

@login_required(login_url='ingia')
@ruhusa_inahitajika('usimamizi.add_hudhurio')
def mahudhurio_darasa(request, darasa_id):
    darasa = get_object_or_404(Darasa, id=darasa_id)
    wanafunzi = Mwanafunzi.objects.active().filter(darasa=darasa).order_by('jina_kamili')
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
@ruhusa_inahitajika('usimamizi.add_hudhurio')
def chukua_mahudhurio_hifdhu(request, somo_id):
    somo = get_object_or_404(Somo, id=somo_id)
    wanafunzi = Mwanafunzi.objects.active().filter(programu_ya_usiku=somo).order_by('jina_kamili')
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

