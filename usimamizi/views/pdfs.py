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

