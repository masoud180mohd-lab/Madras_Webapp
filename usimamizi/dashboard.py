"""
Staff home dashboard — role-gated operational context for mwanzo.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse

from .models import Darasa, Hudhurio, Malipo, Mtihani, Mwanafunzi, Tangazo
from .permissions import (
    CAP_ATTENDANCE,
    CAP_EXAMS,
    CAP_FEES,
    CAP_MANAGE_STUDENTS,
    CAP_PARENT_CONTACT,
    CAP_VIEW_DIRECTORY,
    CAP_VIEW_STUDENTS,
    get_user_cheo,
    user_has_capability,
)


def _display_name(user):
    full = (user.get_full_name() or "").strip()
    return full or user.username


def build_dashboard_context(user, leo=None):
    """Return template context for the staff operational home."""
    leo = leo or date.today()
    cheo = get_user_cheo(user)

    context = {
        "leo": leo,
        "jina_la_mtumiaji": _display_name(user),
        "cheo": cheo,
        "matangazo": list(Tangazo.objects.order_by("-tarehe_iliyotolewa")[:5]),
        "vipimo": [],
        "vitendo_haraka": [],
    }

    if user_has_capability(user, CAP_VIEW_STUDENTS, CAP_VIEW_DIRECTORY):
        context["vipimo"].append(
            {
                "label": "Wanafunzi",
                "value": Mwanafunzi.objects.active().count(),
                "hint": "Walio hai (bila waliohifadhiwa)",
                "url": reverse("orodha_wanafunzi")
                if user_has_capability(user, CAP_VIEW_STUDENTS)
                else reverse("orodha_madarasa"),
            }
        )
        context["vipimo"].append(
            {
                "label": "Madarasa",
                "value": Darasa.objects.count(),
                "hint": "Madarasa yaliyosajiliwa",
                "url": reverse("orodha_madarasa"),
            }
        )

    if user_has_capability(user, CAP_ATTENDANCE):
        madarasa_yenye_wanafunzi = (
            Darasa.objects.annotate(
                n=Count("mwanafunzi", filter=Q(mwanafunzi__amehifadhiwa=False))
            )
            .filter(n__gt=0)
            .count()
        )
        yaliyorekodiwa = (
            Hudhurio.objects.filter(tarehe=leo, aina_ya_rekodi="Kawaida")
            .exclude(mwanafunzi__darasa_id=None)
            .values("mwanafunzi__darasa_id")
            .distinct()
            .count()
        )
        hayupo_leo = Hudhurio.objects.filter(
            tarehe=leo, yupo=False, aina_ya_rekodi="Kawaida"
        ).count()
        context["vipimo"].append(
            {
                "label": "Mahudhurio leo",
                "value": f"{yaliyorekodiwa}/{madarasa_yenye_wanafunzi}",
                "hint": "Madarasa yaliyorekodiwa / yenye wanafunzi",
                "url": reverse("orodha_madarasa"),
            }
        )
        context["vipimo"].append(
            {
                "label": "Hawapo leo",
                "value": hayupo_leo,
                "hint": "Rekodi za utoro (kawaida) leo",
                "url": reverse("ripoti_watoro"),
                "tone": "warning" if hayupo_leo else "ok",
            }
        )

    if user_has_capability(user, CAP_EXAMS):
        since = leo - timedelta(days=30)
        mitihani_karibuni = Mtihani.objects.filter(tarehe__gte=since).count()
        bila_maksi = (
            Mtihani.objects.annotate(n=Count("matokeo")).filter(n=0).count()
        )
        context["vipimo"].append(
            {
                "label": "Mitihani (siku 30)",
                "value": mitihani_karibuni,
                "hint": "Mitihani ya siku 30 zilizopita",
                "url": reverse("orodha_masomo"),
            }
        )
        context["vipimo"].append(
            {
                "label": "Bila maksi",
                "value": bila_maksi,
                "hint": "Mitihani isiyo na matokeo bado",
                "url": reverse("orodha_masomo"),
                "tone": "warning" if bila_maksi else "ok",
            }
        )

    if user_has_capability(user, CAP_FEES):
        malipo_leo = Malipo.objects.filter(tarehe_ya_malipo=leo)
        idadi = malipo_leo.count()
        jumla = malipo_leo.aggregate(
            jumla=Coalesce(
                Sum("kiasi_kilicholipwa"),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )["jumla"] or Decimal("0")
        context["vipimo"].append(
            {
                "label": "Malipo leo",
                "value": idadi,
                "hint": f"Jumla Tsh {jumla:,.0f}/=",
                "url": reverse("malipo"),
            }
        )

    _append_quick_actions(user, context)
    return context


def _append_quick_actions(user, context):
    actions = context["vitendo_haraka"]

    if user_has_capability(user, CAP_MANAGE_STUDENTS):
        actions.append(
            {
                "label": "Sajili mwanafunzi",
                "hint": "Ongeza rekodi mpya",
                "url": reverse("sajili_mwanafunzi"),
            }
        )

    if user_has_capability(user, CAP_ATTENDANCE) or user_has_capability(
        user, CAP_VIEW_DIRECTORY
    ):
        actions.append(
            {
                "label": "Madarasa",
                "hint": "Mahudhurio na orodha",
                "url": reverse("orodha_madarasa"),
            }
        )

    if user_has_capability(user, CAP_ATTENDANCE):
        actions.append(
            {
                "label": "Ripoti ya watoro",
                "hint": "Utoro wa wiki",
                "url": reverse("ripoti_watoro"),
            }
        )

    if user_has_capability(user, CAP_EXAMS) or user_has_capability(
        user, CAP_VIEW_DIRECTORY
    ):
        actions.append(
            {
                "label": "Masomo",
                "hint": "Mitihani na maksi",
                "url": reverse("orodha_masomo"),
            }
        )

    if user_has_capability(user, CAP_FEES):
        actions.append(
            {
                "label": "Malipo",
                "hint": "Ada na risiti",
                "url": reverse("malipo"),
            }
        )

    if user_has_capability(user, CAP_PARENT_CONTACT):
        actions.append(
            {
                "label": "Mawasiliano",
                "hint": "Wazazi na kumbukumbu za simu",
                "url": reverse("orodha_mawasiliano"),
            }
        )

    if user_has_capability(user, CAP_VIEW_STUDENTS):
        actions.append(
            {
                "label": "Wanafunzi",
                "hint": "Orodha kamili",
                "url": reverse("orodha_wanafunzi"),
            }
        )
