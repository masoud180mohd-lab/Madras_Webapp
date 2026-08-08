"""
Staff home dashboard — role-gated operational context for mwanzo.
Ufuatiliaji: deni la ada + mahudhurio (in-app lists — si push notifications).
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse

from .academic import get_active_mwaka
from .models import AinaMalipo, Darasa, Hudhurio, Malipo, Mtihani, Mwanafunzi, Tangazo
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


def _wiki_kuanzia(leo: date) -> date:
    """Jumamosi iliyopita (sawa na ripoti_watoro)."""
    siku = (leo.weekday() - 5) % 7
    if siku == 0:
        siku = 7
    return leo - timedelta(days=siku)


def _build_fee_debt_followup(limit: int = 8) -> dict | None:
    """Aggregate outstanding fee debt for active-year (or unscoped) fee types."""
    mwaka = get_active_mwaka()
    aina_qs = AinaMalipo.objects.select_related("mwaka")
    if mwaka:
        aina_qs = aina_qs.filter(Q(mwaka=mwaka) | Q(mwaka__isnull=True))
    ainas = list(aina_qs.order_by("-mwaka__mwaka_kuanzia", "mwezi", "jina")[:20])
    if not ainas:
        return {
            "idadi": 0,
            "jumla": Decimal("0"),
            "orodha": [],
            "mwaka_jina": mwaka.jina if mwaka else None,
            "malipo_url": reverse("malipo"),
        }

    active = list(
        Mwanafunzi.objects.active()
        .select_related("darasa")
        .only(
            "id",
            "jina_kamili",
            "namba_ya_usajili",
            "darasa_id",
            "darasa__jina",
        )
    )
    if not active:
        return {
            "idadi": 0,
            "jumla": Decimal("0"),
            "orodha": [],
            "mwaka_jina": mwaka.jina if mwaka else None,
            "malipo_url": reverse("malipo"),
        }

    debt_by_student: dict[int, dict] = {}
    for aina in ainas:
        paid_rows = (
            Malipo.objects.filter(aina_ya_malipo=aina)
            .values("mwanafunzi_id")
            .annotate(
                jumla=Coalesce(
                    Sum("kiasi_kilicholipwa"),
                    Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
        )
        paid_map = {row["mwanafunzi_id"]: row["jumla"] or Decimal("0") for row in paid_rows}
        kinachotakiwa = aina.kiasi_kinachotakiwa or Decimal("0")
        for m in active:
            paid = paid_map.get(m.id, Decimal("0"))
            deni = kinachotakiwa - paid
            if deni <= 0:
                continue
            slot = debt_by_student.setdefault(
                m.id,
                {
                    "mwanafunzi": m,
                    "deni": Decimal("0"),
                    "aina_fupi": [],
                    "profile_url": reverse("mwanafunzi_profile", args=[m.id]),
                    "malipo_url": reverse("weka_malipo", args=[m.id, aina.id]),
                },
            )
            slot["deni"] += deni
            label = aina.lebo_kamili
            if label not in slot["aina_fupi"] and len(slot["aina_fupi"]) < 3:
                slot["aina_fupi"].append(label)
            # Keep link pointed at a fee type they still owe
            slot["malipo_url"] = reverse("weka_malipo", args=[m.id, aina.id])

    orodha = sorted(debt_by_student.values(), key=lambda r: r["deni"], reverse=True)
    jumla = sum((r["deni"] for r in orodha), Decimal("0"))
    return {
        "idadi": len(orodha),
        "jumla": jumla,
        "orodha": orodha[:limit],
        "mwaka_jina": mwaka.jina if mwaka else None,
        "malipo_url": reverse("malipo"),
    }


def _build_attendance_followup(leo: date, limit: int = 8) -> dict:
    """Today's absences + week absentee count for follow-up (not notifications)."""
    kuanzia = _wiki_kuanzia(leo)
    hayupo_leo_qs = (
        Hudhurio.objects.filter(tarehe=leo, yupo=False, aina_ya_rekodi="Kawaida")
        .select_related("mwanafunzi", "mwanafunzi__darasa")
        .order_by("mwanafunzi__jina_kamili")
    )
    orodha = []
    for h in hayupo_leo_qs[:limit]:
        m = h.mwanafunzi
        if m.amehifadhiwa:
            continue
        orodha.append(
            {
                "mwanafunzi": m,
                "darasa": m.darasa.jina if m.darasa_id else "—",
                "profile_url": reverse("mwanafunzi_profile", args=[m.id]),
                "mawasiliano_url": reverse("mwanafunzi_mawasiliano", args=[m.id]),
            }
        )

    watoro_wiki = (
        Mwanafunzi.objects.active()
        .filter(
            hudhurio__tarehe__gte=kuanzia,
            hudhurio__yupo=False,
            hudhurio__aina_ya_rekodi="Kawaida",
        )
        .distinct()
        .count()
    )
    hayupo_leo = Hudhurio.objects.filter(
        tarehe=leo,
        yupo=False,
        aina_ya_rekodi="Kawaida",
        mwanafunzi__amehifadhiwa=False,
    ).count()

    return {
        "hayupo_leo": hayupo_leo,
        "watoro_wiki": watoro_wiki,
        "kuanzia": kuanzia,
        "orodha": orodha,
        "watoro_url": reverse("ripoti_watoro"),
        "madarasa_url": reverse("orodha_madarasa"),
    }


def build_dashboard_context(user, leo=None):
    """Return template context for the staff operational home."""
    leo = leo or date.today()
    cheo = get_user_cheo(user)
    anaweza_mawasiliano = user_has_capability(user, CAP_PARENT_CONTACT)

    context = {
        "leo": leo,
        "jina_la_mtumiaji": _display_name(user),
        "cheo": cheo,
        "matangazo": list(Tangazo.objects.order_by("-tarehe_iliyotolewa")[:5]),
        "vipimo": [],
        "vitendo_haraka": [],
        "ufuatiliaji_deni": None,
        "ufuatiliaji_mahudhurio": None,
        "anaweza_mawasiliano": anaweza_mawasiliano,
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
        follow = _build_attendance_followup(leo)
        context["ufuatiliaji_mahudhurio"] = follow
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
                "value": follow["hayupo_leo"],
                "hint": "Utoro wa kawaida leo — ufuatiliaji",
                "url": reverse("ripoti_watoro"),
                "tone": "warning" if follow["hayupo_leo"] else "ok",
            }
        )
        context["vipimo"].append(
            {
                "label": "Watoro wiki",
                "value": follow["watoro_wiki"],
                "hint": f"Kuanzia {follow['kuanzia'].strftime('%d/%m')}",
                "url": reverse("ripoti_watoro"),
                "tone": "warning" if follow["watoro_wiki"] else "ok",
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
        debt = _build_fee_debt_followup()
        context["ufuatiliaji_deni"] = debt
        context["vipimo"].append(
            {
                "label": "Malipo leo",
                "value": idadi,
                "hint": f"Jumla Tsh {jumla:,.0f}/=",
                "url": reverse("malipo"),
            }
        )
        context["vipimo"].append(
            {
                "label": "Wanaodaiwa",
                "value": debt["idadi"],
                "hint": f"Deni Tsh {debt['jumla']:,.0f}/="
                + (f" · {debt['mwaka_jina']}" if debt.get("mwaka_jina") else ""),
                "url": reverse("malipo"),
                "tone": "warning" if debt["idadi"] else "ok",
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
                "hint": "Ufuatiliaji wa mahudhurio",
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
                "hint": "Deni la ada na risiti",
                "url": reverse("malipo"),
            }
        )

    if user_has_capability(user, CAP_PARENT_CONTACT):
        actions.append(
            {
                "label": "Mawasiliano",
                "hint": "Wazazi — simu / WhatsApp",
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
