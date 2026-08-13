"""Batch attendance write — same unique rule as the SSR mahudhurio views."""

from __future__ import annotations

from datetime import date

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import APIException

from usimamizi.audit import andika_ukaguzi_mahudhurio
from usimamizi.models import Darasa, Hudhurio, Mwanafunzi, Somo


class AttendanceAlreadyRecorded(APIException):
    status_code = 409
    default_detail = "Mahudhurio ya siku hii tayari yameshajulikana."
    default_code = "already_recorded"


def _active_roster(*, darasa=None, somo=None):
    qs = Mwanafunzi.objects.active()
    if darasa is not None:
        return qs.filter(darasa=darasa).order_by("jina_kamili")
    return qs.filter(programu_ya_usiku=somo).order_by("jina_kamili")


def _existing_sample(*, darasa, somo, tarehe, aina):
    qs = Hudhurio.objects.filter(tarehe=tarehe, aina_ya_rekodi=aina)
    if aina == "Hifdhu" and somo is not None:
        qs = qs.filter(mwanafunzi__programu_ya_usiku=somo)
    else:
        qs = qs.filter(mwanafunzi__darasa=darasa)
    return qs.select_related("iliyorekodiwa_na").first()


def record_class_attendance(*, user, darasa_id, tarehe, aina_ya_rekodi, rekodi, somo_id=None):
    """
    Create one Hudhurio row per active student in the class/hifdhu group.

    Posted student ids must match the active roster exactly (same as the web grid).
    Raises AttendanceAlreadyRecorded (409) if today's roll already exists.
    """
    aina = aina_ya_rekodi or "Kawaida"
    day = tarehe or date.today()
    darasa = None
    somo = None

    if aina == "Hifdhu":
        if not somo_id:
            raise ValidationError({"somo": "Somo la Hifdhu linahitajika."})
        somo = get_object_or_404(Somo, pk=somo_id)
        wanafunzi = list(_active_roster(somo=somo))
        darasa = somo.darasa
    else:
        darasa = get_object_or_404(Darasa, pk=darasa_id)
        wanafunzi = list(_active_roster(darasa=darasa))

    roster_ids = {m.pk for m in wanafunzi}
    posted_ids = {row["mwanafunzi"] for row in rekodi}
    if posted_ids != roster_ids:
        raise ValidationError(
            {
                "rekodi": (
                    "Rekodi lazima ziwe wanafunzi wote hai wa darasa/somo hili "
                    "(bila kuongeza au kuacha)."
                ),
                "expected_ids": sorted(roster_ids),
            }
        )

    if _existing_sample(darasa=darasa, somo=somo, tarehe=day, aina=aina):
        raise AttendanceAlreadyRecorded()

    by_id = {row["mwanafunzi"]: row for row in rekodi}
    rows = []
    for mwanafunzi in wanafunzi:
        row = by_id[mwanafunzi.pk]
        yupo = bool(row["yupo"])
        sababu = (row.get("sababu_kama_hayupo") or "").strip()
        if yupo:
            sababu = ""
        rows.append(
            Hudhurio(
                mwanafunzi=mwanafunzi,
                yupo=yupo,
                sababu_kama_hayupo=sababu or None,
                aina_ya_rekodi=aina,
                tarehe=day,
                iliyorekodiwa_na=user,
            )
        )

    try:
        with transaction.atomic():
            created = Hudhurio.objects.bulk_create(rows)
            andika_ukaguzi_mahudhurio(
                user=user,
                darasa=darasa,
                somo=somo,
                aina_ya_rekodi=aina,
                idadi=len(created),
                tarehe=day,
            )
    except IntegrityError as exc:
        raise AttendanceAlreadyRecorded() from exc

    return {
        "idadi": len(created),
        "tarehe": day.isoformat(),
        "aina_ya_rekodi": aina,
        "darasa": darasa.pk if darasa else None,
    }
