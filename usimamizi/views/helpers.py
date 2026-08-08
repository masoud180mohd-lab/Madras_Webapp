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

