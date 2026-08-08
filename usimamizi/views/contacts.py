"""Parent/guardian contacts and call log for office follow-up."""

from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from ..forms import MawasilianoContactForm, RekodiSimuMzaziForm
from ..models import Darasa, Mwanafunzi, RekodiSimuMzazi
from ..permissions import CAP_PARENT_CONTACT, ruhusa_capability
from ..whatsapp import (
    TEMPLATE_CHOICES,
    WHATSAPP_TEMPLATES,
    build_wa_me_url,
    message_for_mwanafunzi,
    normalize_phone_tz,
    recipient_whatsapp_row,
)


@login_required(login_url="ingia")
@ruhusa_capability(CAP_PARENT_CONTACT)
def orodha_mawasiliano(request):
    q = (request.GET.get("q") or "").strip()
    darasa_id = request.GET.get("darasa") or ""
    hali = request.GET.get("hali") or "wote"

    qs = (
        Mwanafunzi.objects.active()
        .select_related("darasa")
        .annotate(simu_mwisho=Max("rekodi_simu__tarehe_ya_simu"))
        .order_by("jina_kamili")
    )
    if q:
        qs = qs.filter(
            Q(jina_kamili__icontains=q)
            | Q(namba_ya_usajili__icontains=q)
            | Q(jina_la_mzazi__icontains=q)
            | Q(namba_ya_simu_mzazi__icontains=q)
        )
    if darasa_id.isdigit():
        qs = qs.filter(darasa_id=int(darasa_id))
    if hali == "bila_namba":
        qs = qs.filter(
            Q(namba_ya_simu_mzazi__isnull=True) | Q(namba_ya_simu_mzazi="")
        )
    elif hali == "zina_namba":
        qs = qs.exclude(
            Q(namba_ya_simu_mzazi__isnull=True) | Q(namba_ya_simu_mzazi="")
        )

    simu_za_karibuni = (
        RekodiSimuMzazi.objects.select_related(
            "mwanafunzi", "mwanafunzi__darasa", "iliyorekodiwa_na"
        ).order_by("-tarehe_ya_simu")[:15]
    )

    return render(
        request,
        "usimamizi/orodha_mawasiliano.html",
        {
            "wanafunzi": qs,
            "madarasa": Darasa.objects.all().order_by("jina"),
            "q": q,
            "darasa_filter": darasa_id,
            "hali": hali,
            "simu_za_karibuni": simu_za_karibuni,
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_PARENT_CONTACT)
def mwanafunzi_mawasiliano(request, mwanafunzi_id):
    mwanafunzi = get_object_or_404(
        Mwanafunzi.objects.select_related("darasa"), id=mwanafunzi_id
    )
    contact_form = MawasilianoContactForm(instance=mwanafunzi)
    call_form = RekodiSimuMzaziForm(mwanafunzi=mwanafunzi)
    rekodi = mwanafunzi.rekodi_simu.select_related("iliyorekodiwa_na").all()[:50]

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "sasisha_mawasiliano":
            contact_form = MawasilianoContactForm(request.POST, instance=mwanafunzi)
            if contact_form.is_valid():
                contact_form.save()
                messages.success(request, "Mawasiliano yamesasishwa.")
                return redirect(
                    "mwanafunzi_mawasiliano", mwanafunzi_id=mwanafunzi.id
                )
        elif action == "rekodi_simu":
            call_form = RekodiSimuMzaziForm(
                request.POST, mwanafunzi=mwanafunzi
            )
            if call_form.is_valid():
                row = call_form.save(commit=False)
                row.mwanafunzi = mwanafunzi
                row.iliyorekodiwa_na = request.user
                if not row.namba_iliyopigwa:
                    row.namba_iliyopigwa = mwanafunzi.namba_ya_simu_mzazi or ""
                row.save()
                messages.success(request, "Simu imerekodiwa.")
                return redirect(
                    "mwanafunzi_mawasiliano", mwanafunzi_id=mwanafunzi.id
                )

    e164 = normalize_phone_tz(mwanafunzi.namba_ya_simu_mzazi)
    whatsapp_fungua_url = None
    if e164:
        whatsapp_fungua_url = (
            reverse("fungua_whatsapp", args=[mwanafunzi.id])
            + "?"
            + urlencode({"kigezo": "jumla"})
        )

    return render(
        request,
        "usimamizi/mwanafunzi_mawasiliano.html",
        {
            "mwanafunzi": mwanafunzi,
            "contact_form": contact_form,
            "call_form": call_form,
            "rekodi": rekodi,
            "rudi_url": reverse("orodha_mawasiliano"),
            "ina_whatsapp": bool(e164),
            "whatsapp_fungua_url": whatsapp_fungua_url,
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_PARENT_CONTACT)
@require_http_methods(["POST"])
def rekodi_simu_kutoka_profile(request, mwanafunzi_id):
    """POST from student profile tab — same capability as office page."""
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    form = RekodiSimuMzaziForm(request.POST, mwanafunzi=mwanafunzi)
    if form.is_valid():
        row = form.save(commit=False)
        row.mwanafunzi = mwanafunzi
        row.iliyorekodiwa_na = request.user
        if not row.namba_iliyopigwa:
            row.namba_iliyopigwa = mwanafunzi.namba_ya_simu_mzazi or ""
        row.save()
        messages.success(request, "Simu imerekodiwa.")
    else:
        messages.error(request, "Imeshindikana kurekodi simu — angalia fomu.")
    return redirect(
        f"{reverse('mwanafunzi_profile', args=[mwanafunzi.id])}?tab=mawasiliano"
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_PARENT_CONTACT)
def tuma_whatsapp(request):
    """Campaign UI under Mawasiliano — wa.me links, no auto-send."""
    q = (request.GET.get("q") or "").strip()
    darasa_id = request.GET.get("darasa") or ""
    template_key = request.GET.get("kigezo") or ""
    ujumbe = request.GET.get("ujumbe") or ""
    if not ujumbe and template_key in WHATSAPP_TEMPLATES:
        ujumbe = WHATSAPP_TEMPLATES[template_key]

    qs = (
        Mwanafunzi.objects.active()
        .select_related("darasa")
        .exclude(Q(namba_ya_simu_mzazi__isnull=True) | Q(namba_ya_simu_mzazi=""))
        .order_by("jina_kamili")
    )
    if q:
        qs = qs.filter(
            Q(jina_kamili__icontains=q)
            | Q(namba_ya_usajili__icontains=q)
            | Q(jina_la_mzazi__icontains=q)
            | Q(namba_ya_simu_mzazi__icontains=q)
        )
    if darasa_id.isdigit():
        qs = qs.filter(darasa_id=int(darasa_id))

    rows = [recipient_whatsapp_row(m, ujumbe) for m in qs]
    valid_count = sum(1 for r in rows if r["ina_namba_sahihi"])
    invalid_count = len(rows) - valid_count

    return render(
        request,
        "usimamizi/tuma_whatsapp.html",
        {
            "rows": rows,
            "madarasa": Darasa.objects.all().order_by("jina"),
            "q": q,
            "darasa_filter": darasa_id,
            "ujumbe": ujumbe,
            "kigezo": template_key,
            "template_choices": TEMPLATE_CHOICES,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_PARENT_CONTACT)
@require_GET
def fungua_whatsapp(request, mwanafunzi_id):
    """
    Log WhatsApp outreach as started, then redirect to wa.me.
    Operator must still press Send in WhatsApp — no Business API.
    """
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    e164 = normalize_phone_tz(mwanafunzi.namba_ya_simu_mzazi)
    next_url = request.GET.get("next") or reverse(
        "mwanafunzi_mawasiliano", args=[mwanafunzi.id]
    )
    if not e164:
        messages.error(
            request,
            "Namba ya simu si sahihi au haipo — haiwezi kufungua WhatsApp.",
        )
        return redirect(next_url)

    template_key = request.GET.get("kigezo") or ""
    custom = request.GET.get("ujumbe") or ""
    text = message_for_mwanafunzi(
        mwanafunzi, template_key=template_key, custom_text=custom
    )
    wa_url = build_wa_me_url(e164, text)

    RekodiSimuMzazi.objects.create(
        mwanafunzi=mwanafunzi,
        namba_iliyopigwa=mwanafunzi.namba_ya_simu_mzazi or e164,
        sababu=RekodiSimuMzazi.SABABU_WHATSAPP,
        matokeo=RekodiSimuMzazi.MATOKEO_IMEANZISHWA,
        maelezo=(text[:500] if text else "WhatsApp imeanzishwa"),
        tarehe_ya_simu=timezone.now(),
        iliyorekodiwa_na=request.user,
    )
    return redirect(wa_url)
