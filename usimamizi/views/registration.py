"""Registration hub — sajili mwanafunzi, mwalimu, somo, darasa, mwaka."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..forms import SomoForm
from ..permissions import CAP_MANAGE_STUDENTS, CAP_MSETO, ruhusa_capability, user_has_capability


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS, CAP_MSETO)
def ukurasa_usajili(request):
    """Landing page for all madrasa registration shortcuts."""
    can_manage = user_has_capability(request.user, CAP_MANAGE_STUDENTS)
    can_mwaka = user_has_capability(request.user, CAP_MSETO)
    cards = []
    if can_manage:
        cards.extend(
            [
                {
                    "title": "Sajili mwanafunzi",
                    "copy": "Jaza taarifa za msingi, darasa na mzazi.",
                    "url_name": "sajili_mwanafunzi",
                    "kitufe": "Sajili mwanafunzi",
                },
                {
                    "title": "Sajili mwalimu",
                    "copy": "Unda akaunti na wasifu wa mwalimu.",
                    "url_name": "ongeza_mwalimu",
                    "kitufe": "Sajili mwalimu",
                },
                {
                    "title": "Sajili somo",
                    "copy": "Ongeza somo la darasa au hifdhu.",
                    "url_name": "ongeza_somo",
                    "kitufe": "Sajili somo",
                },
                {
                    "title": "Sajili darasa",
                    "copy": "Unda darasa / ngazi mpya ya madrasa.",
                    "url_name": "ongeza_darasa",
                    "kitufe": "Sajili darasa",
                },
            ]
        )
    if can_mwaka:
        cards.append(
            {
                "title": "Mwaka na muhula",
                "copy": "Unda mwaka, ongeza muhula, na weka kipindi hai.",
                "url_name": "mwaka_masomo",
                "kitufe": "Fungua mwaka",
            }
        )
    return render(
        request,
        "usimamizi/usajili.html",
        {
            "kadi": cards,
            "anaweza_simamia": can_manage,
            "anaweza_mwaka": can_mwaka,
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS)
def ongeza_somo(request):
    if request.method == "POST":
        form = SomoForm(request.POST)
        if form.is_valid():
            somo = form.save()
            messages.success(request, f'Somo "{somo.jina}" limesajiliwa.')
            return redirect("orodha_masomo")
    else:
        form = SomoForm()
    return render(
        request,
        "usimamizi/fomu_usimamizi.html",
        {
            "form": form,
            "kichwa": "Sajili somo",
            "maelezo": "Ongeza somo jipya la darasa au la hifdhu.",
            "kitufe": "Hifadhi somo",
            "rudi_url": "orodha_masomo",
        },
    )
