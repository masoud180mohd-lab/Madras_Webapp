from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ..academic import get_active_muhula, get_active_mwaka, set_active_muhula, set_active_mwaka
from ..forms import MuhulaForm, MwakaWaMasomoForm
from ..models import Muhula, MwakaWaMasomo
from ..permissions import CAP_MSETO, ruhusa_capability


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
