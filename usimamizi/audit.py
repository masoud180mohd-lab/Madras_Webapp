"""Helpers for append-only operational audit (mahudhurio / malipo)."""

from __future__ import annotations

from .models import RekodiUkaguzi


def _display_user(user):
    if not user:
        return "mfumo"
    full = (user.get_full_name() or "").strip()
    return full or user.username


def andika_ukaguzi(
    *,
    user,
    kitendo,
    maelezo,
    darasa=None,
    somo=None,
    mwanafunzi=None,
    malipo=None,
    idadi_ya_rekodi=None,
):
    """Create one audit row. Never raises into the request path if DB write fails? — let it raise."""
    return RekodiUkaguzi.objects.create(
        mtumiaji=user if getattr(user, "is_authenticated", False) else None,
        kitendo=kitendo,
        maelezo=maelezo[:500],
        darasa=darasa,
        somo=somo,
        mwanafunzi=mwanafunzi,
        malipo=malipo,
        idadi_ya_rekodi=idadi_ya_rekodi,
    )


def andika_ukaguzi_mahudhurio(*, user, darasa=None, somo=None, aina_ya_rekodi, idadi, tarehe):
    if aina_ya_rekodi == "Hifdhu":
        kitendo = RekodiUkaguzi.KITENDO_MAHUDHURIO_HIFDHU
        where = f"somo {somo.jina}" if somo else "hifdhu"
    else:
        kitendo = RekodiUkaguzi.KITENDO_MAHUDHURIO_KAWAIDA
        where = f"darasa {darasa.jina}" if darasa else "kawaida"
    maelezo = (
        f"{_display_user(user)} alirekodi mahudhurio ({aina_ya_rekodi}) "
        f"ya {where} tarehe {tarehe:%d/%m/%Y} — rekodi {idadi}."
    )
    return andika_ukaguzi(
        user=user,
        kitendo=kitendo,
        maelezo=maelezo,
        darasa=darasa,
        somo=somo,
        idadi_ya_rekodi=idadi,
    )


def andika_ukaguzi_malipo(*, user, malipo):
    maelezo = (
        f"{_display_user(user)} alirekodi malipo Tsh {malipo.kiasi_kilicholipwa}/= "
        f"kutoka {malipo.mwanafunzi.jina_kamili} ({malipo.aina_ya_malipo.jina})."
    )
    return andika_ukaguzi(
        user=user,
        kitendo=RekodiUkaguzi.KITENDO_MALIPO,
        maelezo=maelezo,
        mwanafunzi=malipo.mwanafunzi,
        malipo=malipo,
        idadi_ya_rekodi=1,
    )


def andika_ukaguzi_hamisha_darasa(
    *,
    user,
    darasa_kutoka,
    darasa_kwenda,
    idadi,
    maezo="",
):
    kutoka = darasa_kutoka.jina if darasa_kutoka else "—"
    kwenda = darasa_kwenda.jina if darasa_kwenda else "—"
    maelezo = (
        f"{_display_user(user)} alihamisha wanafunzi {idadi} "
        f"kutoka {kutoka} kwenda {kwenda}."
    )
    if maezo:
        maelezo = f"{maelezo} Maelezo: {maezo}"
    return andika_ukaguzi(
        user=user,
        kitendo=RekodiUkaguzi.KITENDO_HAMISHA_DARASA,
        maelezo=maelezo,
        darasa=darasa_kwenda,
        idadi_ya_rekodi=idadi,
    )
