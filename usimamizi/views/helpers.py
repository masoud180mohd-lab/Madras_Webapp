import csv
import mimetypes
import os
import shutil
import tempfile
import threading
import uuid
import urllib.request
from contextlib import contextmanager
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

from .media_protected import signed_media_url_for_path

# --- Cloudinary-backed media for PDF generation -----------------------------
#
# xhtml2pdf resolves <img>/link URIs through link_callback, which historically
# returns LOCAL filesystem paths. When media lives on Cloudinary (e.g. Render),
# the local MEDIA_ROOT is empty/ephemeral, so we obtain a short-lived signed URL
# via signed_media_url_for_path() and download it to a temporary file whose path
# is handed back to pisa. We download rather than return the remote URL because
# the existing callback contract is "return a local path" — deterministic across
# xhtml2pdf versions and independent of pisa's optional remote-fetch support.

_pdf_local = threading.local()
_fonts_registered = False


def ensure_pdf_fonts():
    """Register custom brand TrueType fonts into ReportLab once."""
    global _fonts_registered
    if _fonts_registered:
        return
    try:
        font_dir = finders.find("usimamizi/fonts/SourceSans3-Regular.ttf")
        if font_dir:
            base_dir = os.path.dirname(font_dir)
            pdfmetrics.registerFont(TTFont("SourceSans", os.path.join(base_dir, "SourceSans3-Regular.ttf")))
            pdfmetrics.registerFont(TTFont("SourceSans-Bold", os.path.join(base_dir, "SourceSans3-Bold.ttf")))
            pdfmetrics.registerFont(TTFont("SourceSans-Italic", os.path.join(base_dir, "SourceSans3-It.ttf")))
            pdfmetrics.registerFont(TTFont("SourceSans-Semibold", os.path.join(base_dir, "SourceSans3-Semibold.ttf")))

            addMapping("SourceSans", 0, 0, "SourceSans")
            addMapping("SourceSans", 1, 0, "SourceSans-Bold")
            addMapping("SourceSans", 0, 1, "SourceSans-Italic")
            addMapping("SourceSans", 1, 1, "SourceSans-Bold")

            pdfmetrics.registerFont(TTFont("Amiri", os.path.join(base_dir, "Amiri-Regular.ttf")))
            pdfmetrics.registerFont(TTFont("Amiri-Bold", os.path.join(base_dir, "Amiri-Bold.ttf")))
            addMapping("Amiri", 0, 0, "Amiri")
            addMapping("Amiri", 1, 0, "Amiri-Bold")
            addMapping("Amiri", 0, 1, "Amiri")
            addMapping("Amiri", 1, 1, "Amiri-Bold")
            _fonts_registered = True
    except Exception:
        pass


@contextmanager
def pdf_media_tempdir():
    """
    Per-PDF-generation temporary directory for downloaded Cloudinary media.

    Wrap each pisa.CreatePDF(...) call in this context manager so the files that
    link_callback downloads are removed as soon as the PDF bytes are produced.
    Nesting is safe; the innermost active directory is the one used.
    """
    ensure_pdf_fonts()
    tmp_dir = tempfile.mkdtemp(prefix="madrasa_pdf_")
    previous = getattr(_pdf_local, "temp_dir", None)
    _pdf_local.temp_dir = tmp_dir
    try:
        yield tmp_dir
    finally:
        _pdf_local.temp_dir = previous
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _media_relative_path(path):
    """
    Return the MEDIA_ROOT-relative portion of a URI, or None if it is not a
    media URI. Accepts the MEDIA_URL form, an absolute "/media/..." form, and a
    relative "media/..." form.
    """
    prefixes = []
    for candidate in (settings.MEDIA_URL, "/media/", "media/"):
        if candidate and candidate not in prefixes:
            prefixes.append(candidate)
    # Longest prefix first so "/media/x" is never matched by the "media/" form.
    for prefix in sorted(prefixes, key=len, reverse=True):
        if path.startswith(prefix):
            return path[len(prefix):]
    return None


def _download_to_temp(signed_url, media_rel):
    """
    Download a signed Cloudinary URL to a temporary file and return its local
    path, or None on failure.

    Uses the active per-generation temp dir (see pdf_media_tempdir) when one is
    set. LIMITATION: when link_callback runs outside pdf_media_tempdir() (e.g. a
    PDF view that does not wrap CreatePDF), files are written to the system temp
    dir and are NOT removed by this code — they rely on the OS temp cleanup
    policy. Wrap CreatePDF calls in pdf_media_tempdir() for guaranteed cleanup.
    """
    try:
        with urllib.request.urlopen(signed_url, timeout=30) as resp:
            data = resp.read()
            content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
    except Exception:
        return None

    suffix = os.path.splitext(media_rel)[1]
    if not suffix and content_type:
        suffix = mimetypes.guess_extension(content_type) or ""
    if not suffix:
        suffix = ".img"

    tmp_dir = getattr(_pdf_local, "temp_dir", None)
    try:
        if tmp_dir is not None:
            dest = os.path.join(tmp_dir, uuid.uuid4().hex + suffix)
            with open(dest, "wb") as fh:
                fh.write(data)
            return dest
        fd, dest = tempfile.mkstemp(suffix=suffix, prefix="madrasa_pdf_")
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return dest
    except Exception:
        return None


def link_callback(uri, rel):
    parsed_uri = urlparse(uri)
    path = parsed_uri.path or uri

    # Cloudinary-backed media: when enabled, embed the file from a signed URL
    # (downloaded to a temp path) instead of the ephemeral local MEDIA_ROOT.
    # signed_media_url_for_path() returns None when Cloudinary is disabled, the
    # path is empty/unsafe (traversal), or signing fails — in every such case we
    # fall through to the unchanged local behaviour below.
    media_rel = _media_relative_path(path)
    if media_rel is not None:
        signed_url = signed_media_url_for_path(media_rel)
        if signed_url:
            local_path = _download_to_temp(signed_url, media_rel)
            if local_path:
                return local_path

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

