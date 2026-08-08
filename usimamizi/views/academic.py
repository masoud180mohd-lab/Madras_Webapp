from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from ..academic import get_active_muhula, get_active_mwaka, set_active_muhula, set_active_mwaka
from ..audit import andika_ukaguzi_hamisha_darasa
from ..forms import MuhulaForm, MwakaWaMasomoForm
from ..models import Darasa, Muhula, MwakaWaMasomo, Mwanafunzi
from ..permissions import CAP_MSETO, CAP_PROMOTE_CLASS, ruhusa_capability


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MSETO)
def ukurasa_mwaka_masomo(request):
    """Create / select active academic year and term (reporting backbone)."""
    mwaka_form = MwakaWaMasomoForm()
    muhula_form = MuhulaForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "unda_mwaka":
            mwaka_form = MwakaWaMasomoForm(request.POST)
            if mwaka_form.is_valid():
                mwaka = mwaka_form.save()
                messages.success(request, f'Mwaka "{mwaka.jina}" umehifadhiwa.')
                return redirect("mwaka_masomo")
            messages.error(request, "Haiwezekani kuhifadhi mwaka. Angalia fomu.")
        elif action == "unda_muhula":
            muhula_form = MuhulaForm(request.POST)
            if muhula_form.is_valid():
                muhula = muhula_form.save()
                messages.success(request, f'Muhula "{muhula}" umehifadhiwa.')
                return redirect("mwaka_masomo")
            messages.error(request, "Haiwezekani kuhifadhi muhula. Angalia fomu.")
        elif action == "weka_mwaka_hai":
            mwaka = get_object_or_404(MwakaWaMasomo, id=request.POST.get("mwaka_id"))
            set_active_mwaka(mwaka)
            messages.success(request, f'Mwaka "{mwaka.jina}" sasa ni hai.')
            return redirect("mwaka_masomo")
        elif action == "weka_muhula_hai":
            muhula = get_object_or_404(Muhula, id=request.POST.get("muhula_id"))
            set_active_muhula(muhula)
            messages.success(request, f'Muhula "{muhula}" sasa ni hai.')
            return redirect("mwaka_masomo")

    miaka = MwakaWaMasomo.objects.prefetch_related("muhula").all()
    return render(
        request,
        "usimamizi/mwaka_masomo.html",
        {
            "miaka": miaka,
            "mwaka_hai": get_active_mwaka(),
            "muhula_hai": get_active_muhula(),
            "mwaka_form": mwaka_form,
            "muhula_form": muhula_form,
        },
    )


def _parse_student_ids(raw_ids):
    ids = []
    for value in raw_ids:
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            continue
    return ids


@login_required(login_url="ingia")
@ruhusa_capability(CAP_PROMOTE_CLASS)
def hamisha_darasa(request):
    """
    Year-end class promotion: move active students from one Darasa to another.
    GET / POST hakiki → confirm · POST thibitisha → atomic update + audit.
    """
    madarasa = Darasa.objects.order_by("jina")
    kutoka_id = request.GET.get("kutoka") or request.POST.get("kutoka") or ""
    kwenda_id = request.POST.get("kwenda") or request.GET.get("kwenda") or ""
    maezo = (request.POST.get("maezo") or "").strip()

    darasa_kutoka = None
    if kutoka_id:
        darasa_kutoka = get_object_or_404(Darasa, id=kutoka_id)

    wanafunzi = []
    if darasa_kutoka:
        wanafunzi = list(
            Mwanafunzi.objects.active()
            .filter(darasa=darasa_kutoka)
            .order_by("jina_kamili")
        )

    if request.method == "POST":
        action = request.POST.get("action")
        darasa_kwenda = get_object_or_404(Darasa, id=request.POST.get("kwenda"))
        selected_ids = _parse_student_ids(request.POST.getlist("wanafunzi"))

        if str(darasa_kwenda.id) == str(kutoka_id):
            messages.error(request, "Darasa la kwenda haliwezi kuwa sawa na la kutoka.")
            return redirect(f"{request.path}?kutoka={kutoka_id}")

        if not selected_ids:
            messages.error(request, "Chagua angalau mwanafunzi mmoja.")
            return redirect(f"{request.path}?kutoka={kutoka_id}")

        candidates = list(
            Mwanafunzi.objects.active().filter(
                id__in=selected_ids,
                darasa_id=kutoka_id,
            )
        )
        if not candidates:
            messages.error(
                request,
                "Hakuna wanafunzi waliochaguliwa wanaolingana na darasa la kutoka.",
            )
            return redirect(f"{request.path}?kutoka={kutoka_id}")

        if action == "hakiki":
            return render(
                request,
                "usimamizi/hamisha_darasa_thibitisha.html",
                {
                    "darasa_kutoka": darasa_kutoka,
                    "darasa_kwenda": darasa_kwenda,
                    "wanafunzi": candidates,
                    "maezo": maezo,
                    "idadi": len(candidates),
                },
            )

        if action == "thibitisha":
            with transaction.atomic():
                updated = Mwanafunzi.objects.active().filter(
                    id__in=[s.id for s in candidates],
                    darasa_id=kutoka_id,
                ).update(darasa=darasa_kwenda)
                andika_ukaguzi_hamisha_darasa(
                    user=request.user,
                    darasa_kutoka=darasa_kutoka,
                    darasa_kwenda=darasa_kwenda,
                    idadi=updated,
                    maezo=maezo,
                )
            messages.success(
                request,
                f"{updated} wanafunzi wamehamishwa kutoka "
                f'"{darasa_kutoka.jina}" kwenda "{darasa_kwenda.jina}".',
            )
            return redirect("hamisha_darasa")

        messages.error(request, "Kitendo hakijatambulika.")
        return redirect("hamisha_darasa")

    return render(
        request,
        "usimamizi/hamisha_darasa.html",
        {
            "madarasa": madarasa,
            "kutoka_id": str(kutoka_id) if kutoka_id else "",
            "kwenda_id": str(kwenda_id) if kwenda_id else "",
            "darasa_kutoka": darasa_kutoka,
            "wanafunzi": wanafunzi,
        },
    )
