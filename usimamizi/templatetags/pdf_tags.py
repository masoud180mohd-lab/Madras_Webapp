from __future__ import annotations

from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def pesa(value) -> str:
    """Format numeric values as Tanzanian Shillings with thousands separator and two decimal places."""
    if value is None or value == "":
        return "0.00"
    try:
        val = Decimal(str(value))
        return f"{val:,.2f}"
    except (ValueError, TypeError):
        return str(value)


@register.filter
def receipt_num(value) -> str:
    """Format receipt ID with clean zero-padding to 5 digits, e.g. REC-00482."""
    if value is None or value == "":
        return "REC-00000"
    try:
        val_int = int(value)
        return f"REC-{val_int:05d}"
    except (ValueError, TypeError):
        return f"REC-{value}"
