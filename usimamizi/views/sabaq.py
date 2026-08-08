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

