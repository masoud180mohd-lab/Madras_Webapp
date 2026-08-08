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

