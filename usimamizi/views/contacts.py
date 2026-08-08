"""Parent/guardian contacts and call log for office follow-up."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..forms import MawasilianoContactForm, RekodiSimuMzaziForm
from ..models import Darasa, Mwanafunzi, RekodiSimuMzazi
from ..permissions import CAP_PARENT_CONTACT, ruhusa_capability


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

    return render(
        request,
        "usimamizi/mwanafunzi_mawasiliano.html",
        {
            "mwanafunzi": mwanafunzi,
            "contact_form": contact_form,
            "call_form": call_form,
            "rekodi": rekodi,
            "rudi_url": reverse("orodha_mawasiliano"),
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_PARENT_CONTACT)
@require_POST
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
