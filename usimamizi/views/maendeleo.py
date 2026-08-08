"""Day-class progress (maendeleo ya mchana) — sabaq-parity for non-hifdhu subjects."""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..forms import MaendeleoMchanaForm
from ..models import Mwanafunzi, RekodiMaendeleoMchana, Somo
from ..permissions import (
    CAP_SABAQ,
    CAP_VIEW_STUDENTS,
    require_linked_mwalimu,
    ruhusa_capability,
    user_has_capability,
)


@login_required(login_url="ingia")
@ruhusa_capability(CAP_VIEW_STUDENTS, CAP_SABAQ)
def wanafunzi_maendeleo_mchana(request, somo_id):
    somo = get_object_or_404(
        Somo.objects.select_related("darasa", "mwalimu"), id=somo_id
    )
    if somo.ni_la_hifdhu:
        messages.info(
            request,
            "Somo la hifdhu linatumia Sabaq — si maendeleo ya mchana.",
        )
        return redirect("wanafunzi_hifdhu", somo_id=somo.id)
    if not somo.darasa_id:
        messages.error(
            request,
            f'Somo "{somo.jina}" halijaunganishwa na darasa — '
            "unganisha darasa kwanza ili kurekodi maendeleo.",
        )
        return redirect("somo_detail", somo_id=somo.id)

    wanafunzi = (
        Mwanafunzi.objects.active()
        .filter(darasa=somo.darasa)
        .order_by("jina_kamili")
    )
    return render(
        request,
        "usimamizi/wanafunzi_maendeleo_mchana.html",
        {
            "somo": somo,
            "wanafunzi": wanafunzi,
            "anaweza_sabaq": user_has_capability(request.user, CAP_SABAQ),
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_SABAQ)
def rekodi_maendeleo_mchana(request, mwanafunzi_id, somo_id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    somo = get_object_or_404(Somo.objects.select_related("darasa"), id=somo_id)

    if mwanafunzi.amehifadhiwa:
        messages.error(
            request,
            "Mwanafunzi huyu amehifadhiwa — huwezi kurekodi maendeleo mapya.",
        )
        return redirect("mwanafunzi_profile", mwanafunzi_id=mwanafunzi.id)
    if somo.ni_la_hifdhu:
        messages.error(request, "Tumia Sabaq kwa somo la hifdhu.")
        return redirect("somo_detail", somo_id=somo.id)
    if somo.darasa_id and mwanafunzi.darasa_id != somo.darasa_id:
        messages.error(
            request,
            "Mwanafunzi hayuko katika darasa la somo hili.",
        )
        return redirect("wanafunzi_maendeleo_mchana", somo_id=somo.id)

    mwalimu = require_linked_mwalimu(request)
    if mwalimu is None:
        return redirect("mwanzo")

    if request.method == "POST":
        form = MaendeleoMchanaForm(request.POST)
        if form.is_valid():
            row = form.save(commit=False)
            row.mwanafunzi = mwanafunzi
            row.somo = somo
            row.mwalimu = mwalimu
            row.save()
            messages.success(
                request,
                f'Maendeleo ya "{somo.jina}" yamehifadhiwa.',
            )
            return redirect("wanafunzi_maendeleo_mchana", somo_id=somo.id)
    else:
        form = MaendeleoMchanaForm()

    return render(
        request,
        "usimamizi/rekodi_maendeleo_mchana.html",
        {
            "form": form,
            "mwanafunzi": mwanafunzi,
            "somo": somo,
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_VIEW_STUDENTS)
def ripoti_maendeleo_mchana(request, mwanafunzi_id):
    mwanafunzi = get_object_or_404(Mwanafunzi, id=mwanafunzi_id)
    qs = (
        RekodiMaendeleoMchana.objects.filter(mwanafunzi=mwanafunzi)
        .select_related("somo", "mwalimu__user")
        .order_by("-tarehe", "-id")
    )
    somo_id = request.GET.get("somo") or ""
    muda = request.GET.get("muda", "wote")
    leo = timezone.now().date()

    if somo_id.isdigit():
        qs = qs.filter(somo_id=int(somo_id))
    if muda == "wiki":
        qs = qs.filter(tarehe__gte=leo - timedelta(days=7))
    elif muda == "mwezi_huu":
        qs = qs.filter(tarehe__year=leo.year, tarehe__month=leo.month)
    elif muda == "mwezi_uliopita":
        mwezi = leo.month - 1 if leo.month > 1 else 12
        mwaka = leo.year if leo.month > 1 else leo.year - 1
        qs = qs.filter(tarehe__year=mwaka, tarehe__month=mwezi)

    masomo = (
        Somo.objects.filter(maendeleo_mchana__mwanafunzi=mwanafunzi)
        .distinct()
        .order_by("jina")
    )

    return render(
        request,
        "usimamizi/ripoti_maendeleo_mchana.html",
        {
            "mwanafunzi": mwanafunzi,
            "rekodi": qs,
            "masomo": masomo,
            "somo_filter": somo_id,
            "muda_teule": muda,
        },
    )
