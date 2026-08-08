"""Regular WhatsApp (wa.me) helpers — no Business API."""

from __future__ import annotations

from urllib.parse import quote

WHATSAPP_TEMPLATES = {
    "ada": (
        "Assalamu alaikum. Hii ni ujumbe kutoka Al-Madrasatul Rasulillah (Mwera) "
        "kuhusu ada/malipo ya {jina} ({mr}). Tafadhali wasiliana na ofisi kwa ufuatiliaji. Jazakumullahu khayran."
    ),
    "mahudhurio": (
        "Assalamu alaikum. Hii ni ujumbe kutoka Al-Madrasatul Rasulillah (Mwera) "
        "kuhusu mahudhurio ya {jina} ({mr}). Tafadhali wasiliana na ofisi. Jazakumullahu khayran."
    ),
    "jumla": (
        "Assalamu alaikum. Hii ni ujumbe kutoka Al-Madrasatul Rasulillah (Mwera) "
        "kwa mzazi/mlezi wa {jina} ({mr}). Tafadhali wasiliana na ofisi. Jazakumullahu khayran."
    ),
}

TEMPLATE_CHOICES = (
    ("", "Andika mwenyewe"),
    ("ada", "Ada ya mwezi"),
    ("mahudhurio", "Mahudhurio"),
    ("jumla", "Habari za jumla"),
)


def normalize_phone_tz(raw: str | None) -> str | None:
    """
    Normalize a TZ-friendly phone to E.164 digits without '+'.
    Examples: 0777123456 → 255777123456; +255 777 123 456 → 255777123456.
    Returns None if unusable.
    """
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if s.startswith("+"):
        s = s[1:]
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return None

    if digits.startswith("0") and len(digits) == 10:
        digits = "255" + digits[1:]
    elif digits.startswith("255"):
        pass
    elif len(digits) == 9 and digits[0] in "67":
        # 777123456 / 622... local without leading 0
        digits = "255" + digits
    else:
        # Already international other country, or odd length — keep if long enough
        if len(digits) < 10:
            return None

    if not (10 <= len(digits) <= 15):
        return None
    return digits


def build_wa_me_url(phone_e164: str, text: str = "") -> str:
    """Build https://wa.me/<digits>?text=... (operator must Send in WhatsApp)."""
    base = f"https://wa.me/{phone_e164}"
    if text:
        return f"{base}?text={quote(text)}"
    return base


def message_for_mwanafunzi(mwanafunzi, template_key: str = "", custom_text: str = "") -> str:
    """Resolve campaign/detail message; placeholders {jina} {mr}."""
    jina = mwanafunzi.jina_kamili
    mr = mwanafunzi.namba_ya_usajili or "—"
    text = (custom_text or "").strip()
    if not text and template_key in WHATSAPP_TEMPLATES:
        text = WHATSAPP_TEMPLATES[template_key]
    if not text:
        text = WHATSAPP_TEMPLATES["jumla"]
    return text.replace("{jina}", jina).replace("{mr}", mr)


def recipient_whatsapp_row(mwanafunzi, text: str) -> dict:
    """Attach normalized phone + wa.me URL (or invalid flag) for list rendering."""
    e164 = normalize_phone_tz(mwanafunzi.namba_ya_simu_mzazi)
    if not e164:
        return {
            "mwanafunzi": mwanafunzi,
            "e164": None,
            "wa_url": None,
            "namba_onyesho": (mwanafunzi.namba_ya_simu_mzazi or "").strip() or None,
            "ina_namba_sahihi": False,
        }
    personalized = message_for_mwanafunzi(mwanafunzi, custom_text=text)
    return {
        "mwanafunzi": mwanafunzi,
        "e164": e164,
        "wa_url": build_wa_me_url(e164, personalized),
        "namba_onyesho": mwanafunzi.namba_ya_simu_mzazi,
        "ina_namba_sahihi": True,
    }
