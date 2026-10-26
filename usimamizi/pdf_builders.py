"""Shared PDF generation for web + mobile API."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from django.utils.timezone import localtime
from xhtml2pdf import pisa

from usimamizi.models import Darasa, Hudhurio, Malipo, Matokeo, MsetoMtihani, Mtihani, RekodiHifdhu
from usimamizi.utils import hesabu_daraja, jenga_ripoti_jumla
from usimamizi.views.helpers import link_callback, pdf_media_tempdir


def build_risiti_pdf_response(malipo: Malipo) -> HttpResponse:
    mwanafunzi = malipo.mwanafunzi
    aina = malipo.aina_ya_malipo
    jumla_yake = (
        Malipo.objects.filter(mwanafunzi=mwanafunzi, aina_ya_malipo=aina)
        .aggregate(
            jumla=Coalesce(
                Sum("kiasi_kilicholipwa"),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )["jumla"]
        or Decimal("0")
    )
    deni_lililobaki = aina.kiasi_kinachotakiwa - jumla_yake
    context = {
        "malipo": malipo,
        "jumla_yake": jumla_yake,
        "deni_lililobaki": deni_lililobaki,
        "wakati_huu": localtime(timezone.now()),
    }
    html = get_template("usimamizi/pdf_risiti.html").render(context)
    response = HttpResponse(content_type="application/pdf")
    jina = f"Risiti_{mwanafunzi.namba_ya_usajili}_{malipo.id}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{jina}"'
    with pdf_media_tempdir():
        if pisa.CreatePDF(html, dest=response, link_callback=link_callback).err:
            return HttpResponse("Kumetokea hitilafu katika kutengeneza Risiti", status=500)
    return response


def build_mahudhurio_pdf_response(mwanafunzi, aina: str, muda: str) -> HttpResponse:
    aina_hudhurio = "Kawaida" if aina == "Darasa" else "Hifdhu"
    mahudhurio = Hudhurio.objects.filter(
        mwanafunzi=mwanafunzi, aina_ya_rekodi=aina_hudhurio
    ).order_by("-tarehe")

    leo = timezone.now().date()
    if muda == "wiki":
        mahudhurio = mahudhurio.filter(tarehe__gte=leo - timedelta(days=7))
    elif muda == "mwezi_huu":
        mahudhurio = mahudhurio.filter(tarehe__year=leo.year, tarehe__month=leo.month)
    elif muda == "mwezi_uliopita":
        mwezi_uliopita = leo.month - 1 if leo.month > 1 else 12
        mwaka = leo.year if leo.month > 1 else leo.year - 1
        mahudhurio = mahudhurio.filter(tarehe__year=mwaka, tarehe__month=mwezi_uliopita)

    muda_wa_sasa = localtime(timezone.now())
    context = {
        "mwanafunzi": mwanafunzi,
        "mahudhurio": mahudhurio,
        "aina": aina,
        "muda": muda,
        "wakati_huu": muda_wa_sasa,
    }
    html = get_template("usimamizi/pdf_mahudhurio.html").render(context)
    response = HttpResponse(content_type="application/pdf")
    jina = f"Mahudhurio_{mwanafunzi.namba_ya_usajili}_{muda_wa_sasa.strftime('%H%M%S')}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{jina}"'
    with pdf_media_tempdir():
        if pisa.CreatePDF(html, dest=response, link_callback=link_callback).err:
            return HttpResponse(
                "Samahani, kumetokea hitilafu katika kutengeneza PDF", status=500
            )
    return response


def build_sabaq_pdf_response(mwanafunzi, aina: str, muda: str) -> HttpResponse:
    sabaq = (
        RekodiHifdhu.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi=aina)
        .prefetch_related("mapande")
        .order_by("-tarehe")
    )
    leo = timezone.now().date()
    if muda == "wiki":
        sabaq = sabaq.filter(tarehe__gte=leo - timedelta(days=7))
    elif muda == "mwezi_huu":
        sabaq = sabaq.filter(tarehe__year=leo.year, tarehe__month=leo.month)
    elif muda == "mwezi_uliopita":
        mwezi_uliopita = leo.month - 1 if leo.month > 1 else 12
        mwaka = leo.year if leo.month > 1 else leo.year - 1
        sabaq = sabaq.filter(tarehe__year=mwaka, tarehe__month=mwezi_uliopita)

    muda_wa_sasa = localtime(timezone.now())
    context = {
        "mwanafunzi": mwanafunzi,
        "sabaq": sabaq,
        "aina": aina,
        "wakati_huu": muda_wa_sasa,
    }
    html = get_template("usimamizi/pdf_sabaq.html").render(context)
    response = HttpResponse(content_type="application/pdf")
    jina = f"Sabaq_{mwanafunzi.namba_ya_usajili}_{muda_wa_sasa.strftime('%H%M%S')}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{jina}"'
    with pdf_media_tempdir():
        if pisa.CreatePDF(html, dest=response, link_callback=link_callback).err:
            return HttpResponse("Hitilafu ilitokea", status=500)
    return response


def build_matokeo_pdf_response(mtihani: Mtihani) -> HttpResponse:
    somo = mtihani.somo
    matokeo_yote = (
        Matokeo.objects.filter(mtihani=mtihani)
        .select_related("mwanafunzi")
        .order_by("-maksi")
    )
    orodha_iliyopangwa = []
    nafasi = 1
    for matokeo in matokeo_yote:
        daraja, maelezo, _ = hesabu_daraja(matokeo.maksi)
        orodha_iliyopangwa.append(
            {
                "mwanafunzi": matokeo.mwanafunzi,
                "maksi": matokeo.maksi,
                "daraja": daraja,
                "maelezo": maelezo,
                "nafasi": nafasi,
            }
        )
        nafasi += 1

    context = {
        "mtihani": mtihani,
        "somo": somo,
        "matokeo": orodha_iliyopangwa,
        "idadi_waliofanya": matokeo_yote.count(),
        "wakati_huu": localtime(timezone.now()),
    }
    html = get_template("usimamizi/pdf_matokeo.html").render(context)
    response = HttpResponse(content_type="application/pdf")
    jina = f"Matokeo_{somo.jina}_{mtihani.jina_la_mtihani}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{jina}"'
    with pdf_media_tempdir():
        if pisa.CreatePDF(html, dest=response, link_callback=link_callback).err:
            return HttpResponse(
                "Kumetokea hitilafu katika kutengeneza PDF ya matokeo", status=500
            )
    return response


def build_matokeo_jumla_pdf_response(darasa: Darasa, mseto: MsetoMtihani) -> HttpResponse:
    ripoti = jenga_ripoti_jumla(mseto)
    for somo in ripoti["masomo"]:
        somo.jina_pdf = somo.jina.replace("_", " ")

    context = {
        "darasa": darasa,
        "mseto": mseto,
        "wakati_huu": localtime(timezone.now()),
        **ripoti,
    }
    html = get_template("usimamizi/pdf_matokeo_jumla.html").render(context)
    response = HttpResponse(content_type="application/pdf")
    jina_salama = mseto.jina.replace(" ", "_")
    jina_la_faili = f"Matokeo_Jumla_{darasa.jina}_{jina_salama}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{jina_la_faili}"'
    with pdf_media_tempdir():
        if pisa.CreatePDF(html, dest=response, link_callback=link_callback).err:
            return HttpResponse(
                "Kumetokea hitilafu katika kutengeneza PDF ya matokeo ya jumla",
                status=500,
            )
    return response
