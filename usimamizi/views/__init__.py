from .helpers import link_callback, paginate_items
from .auth import ingia, toka, ukurasa_wa_mwanzo
from .students import (
    orodha_wanafunzi,
    sajili_mwanafunzi,
    hariri_mwanafunzi,
    orodha_walimu,
    orodha_madarasa,
    wanafunzi_darasa,
    mwanafunzi_profile,
    ripoti_watoro,
)
from .attendance import mahudhurio_darasa, chukua_mahudhurio_hifdhu
from .subjects import (
    orodha_masomo,
    somo_detail,
    wanafunzi_hifdhu,
    pakia_nyenzo,
    ongeza_mtihani,
)
from .sabaq import rekodi_sabaq, ripoti_mwanafunzi
from .exams import (
    weka_maksi,
    tazama_matokeo,
    pakua_pdf_matokeo,
    mseto_mitihani_darasa,
    ripoti_jumla,
    pakua_pdf_matokeo_jumla,
    pakua_csv_matokeo_jumla,
)
from .academic import ukurasa_mwaka_masomo
from .payments import ukurasa_malipo, weka_malipo, pakua_risiti
from .pdfs import pakua_pdf_mahudhurio, pakua_pdf_sabaq

__all__ = [
    "link_callback",
    "paginate_items",
    "ingia",
    "toka",
    "ukurasa_wa_mwanzo",
    "orodha_wanafunzi",
    "sajili_mwanafunzi",
    "hariri_mwanafunzi",
    "orodha_walimu",
    "orodha_madarasa",
    "wanafunzi_darasa",
    "mwanafunzi_profile",
    "ripoti_watoro",
    "mahudhurio_darasa",
    "chukua_mahudhurio_hifdhu",
    "orodha_masomo",
    "somo_detail",
    "wanafunzi_hifdhu",
    "pakia_nyenzo",
    "ongeza_mtihani",
    "rekodi_sabaq",
    "ripoti_mwanafunzi",
    "weka_maksi",
    "tazama_matokeo",
    "pakua_pdf_matokeo",
    "mseto_mitihani_darasa",
    "ripoti_jumla",
    "pakua_pdf_matokeo_jumla",
    "pakua_csv_matokeo_jumla",
    "ukurasa_mwaka_masomo",
    "ukurasa_malipo",
    "weka_malipo",
    "pakua_risiti",
    "pakua_pdf_mahudhurio",
    "pakua_pdf_sabaq",
]
