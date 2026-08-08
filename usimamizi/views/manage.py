"""In-app CRUD for Mwalimu Mkuu: madarasa, walimu, aina za ada."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..academic import get_active_mwaka
from ..forms import AinaMalipoForm, DarasaForm, MwalimuCreateForm, MwalimuEditForm
from ..models import AinaMalipo, Darasa, Malipo, Mwalimu, MwakaWaMasomo, Mwanafunzi, Somo
from ..permissions import CAP_MANAGE_STUDENTS, ruhusa_capability


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS)
def ongeza_darasa(request):
    if request.method == "POST":
        form = DarasaForm(request.POST)
        if form.is_valid():
            darasa = form.save()
            messages.success(request, f'Darasa "{darasa.jina}" limeongezwa.')
            return redirect("orodha_madarasa")
    else:
        form = DarasaForm()
    return render(
        request,
        "usimamizi/fomu_usimamizi.html",
        {
            "form": form,
            "kichwa": "Ongeza darasa",
            "maelezo": "Sajili darasa jipya la madrasa.",
            "kitufe": "Hifadhi darasa",
            "rudi_url": "orodha_madarasa",
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS)
def hariri_darasa(request, darasa_id):
    darasa = get_object_or_404(Darasa, id=darasa_id)
    if request.method == "POST":
        form = DarasaForm(request.POST, instance=darasa)
        if form.is_valid():
            form.save()
            messages.success(request, f'Darasa "{darasa.jina}" limesasishwa.')
            return redirect("orodha_madarasa")
    else:
        form = DarasaForm(instance=darasa)
    return render(
        request,
        "usimamizi/fomu_usimamizi.html",
        {
            "form": form,
            "kichwa": "Hariri darasa",
            "maelezo": darasa.jina,
            "kitufe": "Hifadhi mabadiliko",
            "rudi_url": "orodha_madarasa",
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS)
@require_POST
def futa_darasa(request, darasa_id):
    darasa = get_object_or_404(Darasa, id=darasa_id)
    if Mwanafunzi.objects.filter(darasa=darasa).exists():
        messages.error(
            request,
            f'Huwezi kufuta "{darasa.jina}" — kuna wanafunzi waliohusishwa.',
        )
        return redirect("orodha_madarasa")
    if Somo.objects.filter(darasa=darasa).exists():
        messages.error(
            request,
            f'Huwezi kufuta "{darasa.jina}" — kuna masomo yaliyohusishwa.',
        )
        return redirect("orodha_madarasa")
    jina = darasa.jina
    darasa.delete()
    messages.success(request, f'Darasa "{jina}" limefutwa.')
    return redirect("orodha_madarasa")


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS)
def ongeza_mwalimu(request):
    if request.method == "POST":
        form = MwalimuCreateForm(request.POST, request.FILES)
        if form.is_valid():
            mwalimu = form.save()
            messages.success(
                request,
                f'Mwalimu "{mwalimu}" amesajiliwa. Anaweza kuingia kwa akaunti yake.',
            )
            return redirect("orodha_walimu")
    else:
        form = MwalimuCreateForm()
    return render(
        request,
        "usimamizi/fomu_mwalimu.html",
        {
            "form": form,
            "kichwa": "Sajili mwalimu",
            "maelezo": "Unda akaunti na wasifu wa mwalimu.",
            "kitufe": "Sajili mwalimu",
            "ni_mpya": True,
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS)
def hariri_mwalimu(request, mwalimu_id):
    mwalimu = get_object_or_404(Mwalimu.objects.select_related("user"), id=mwalimu_id)
    if request.method == "POST":
        form = MwalimuEditForm(request.POST, request.FILES, instance=mwalimu)
        if form.is_valid():
            form.save()
            messages.success(request, f'Taarifa za "{mwalimu}" zimesasishwa.')
            return redirect("orodha_walimu")
    else:
        form = MwalimuEditForm(instance=mwalimu)
    return render(
        request,
        "usimamizi/fomu_mwalimu.html",
        {
            "form": form,
            "mwalimu": mwalimu,
            "kichwa": "Hariri mwalimu",
            "maelezo": mwalimu.user.username,
            "kitufe": "Hifadhi mabadiliko",
            "ni_mpya": False,
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS)
def orodha_aina_malipo(request):
    active = get_active_mwaka()
    mwaka_filter = request.GET.get("mwaka") or (
        str(active.id) if active else "yote"
    )
    aina = AinaMalipo.objects.select_related("mwaka").all()
    if mwaka_filter == "bila":
        aina = aina.filter(mwaka__isnull=True)
    elif mwaka_filter != "yote" and str(mwaka_filter).isdigit():
        aina = aina.filter(mwaka_id=int(mwaka_filter))
    aina = aina.order_by("-mwaka__mwaka_kuanzia", "mwezi", "jina")
    return render(
        request,
        "usimamizi/orodha_aina_malipo.html",
        {
            "aina_za_malipo": aina,
            "miaka": MwakaWaMasomo.objects.all().order_by("-mwaka_kuanzia"),
            "mwaka_filter": mwaka_filter,
            "mwaka_hai": active,
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS)
def ongeza_aina_malipo(request):
    if request.method == "POST":
        form = AinaMalipoForm(request.POST)
        if form.is_valid():
            aina = form.save()
            messages.success(request, f'Aina ya malipo "{aina.jina}" imeongezwa.')
            return redirect("orodha_aina_malipo")
    else:
        form = AinaMalipoForm()
    return render(
        request,
        "usimamizi/fomu_usimamizi.html",
        {
            "form": form,
            "kichwa": "Ongeza aina ya ada",
            "maelezo": "Chagua mwaka (na mwezi hiari) ili ada ya Aprili isichanganywe na miaka tofauti.",
            "kitufe": "Hifadhi",
            "rudi_url": "orodha_aina_malipo",
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS)
def hariri_aina_malipo(request, aina_id):
    aina = get_object_or_404(AinaMalipo, id=aina_id)
    if request.method == "POST":
        form = AinaMalipoForm(request.POST, instance=aina)
        if form.is_valid():
            form.save()
            messages.success(request, f'Aina "{aina.jina}" imesasishwa.')
            return redirect("orodha_aina_malipo")
    else:
        form = AinaMalipoForm(instance=aina)
    return render(
        request,
        "usimamizi/fomu_usimamizi.html",
        {
            "form": form,
            "kichwa": "Hariri aina ya ada",
            "maelezo": aina.jina,
            "kitufe": "Hifadhi mabadiliko",
            "rudi_url": "orodha_aina_malipo",
        },
    )


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS)
@require_POST
def futa_aina_malipo(request, aina_id):
    aina = get_object_or_404(AinaMalipo, id=aina_id)
    if Malipo.objects.filter(aina_ya_malipo=aina).exists():
        messages.error(
            request,
            f'Huwezi kufuta "{aina.jina}" — kuna malipo yaliyorekodiwa.',
        )
        return redirect("orodha_aina_malipo")
    jina = aina.jina
    aina.delete()
    messages.success(request, f'Aina "{jina}" imefutwa.')
    return redirect("orodha_aina_malipo")
