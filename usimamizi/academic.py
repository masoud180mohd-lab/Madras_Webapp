"""Active academic year / term helpers."""

from __future__ import annotations

from .models import Muhula, MwakaWaMasomo


def get_active_mwaka():
    return MwakaWaMasomo.objects.filter(ni_hai=True).first()


def get_active_muhula():
    return (
        Muhula.objects.filter(ni_hai=True)
        .select_related("mwaka")
        .first()
    )


def set_active_mwaka(mwaka):
    """Mark one year active; clear other years' active flag (terms stay until reselected)."""
    mwaka.ni_hai = True
    mwaka.save(update_fields=["ni_hai"])
    return mwaka


def set_active_muhula(muhula):
    """Mark one term active and keep its parent year active."""
    muhula.ni_hai = True
    muhula.save()
    return muhula
