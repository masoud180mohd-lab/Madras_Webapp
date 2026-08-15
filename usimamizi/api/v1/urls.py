from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from usimamizi.api.v1.catalog import (
    AinaMalipoListView,
    HamishaPreviewView,
    MalipoListView,
    MawasilianoListView,
    MwakaListView,
    MwanafunziDetailView,
    MwanzoView,
    WanafunziListView,
    WalimuListView,
    WatoroView,
    UkaguziListView,
)
from usimamizi.api.v1.views import (
    DarasaListView,
    DarasaWanafunziView,
    MaendeleoCreateView,
    MahudhurioView,
    MeView,
    MtihaniListView,
    MtihaniMatokeoView,
    SabaqCreateView,
    SomoDetailView,
    SomoListView,
)

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="api_v1_token"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="api_v1_token_refresh"),
    path("me/", MeView.as_view(), name="api_v1_me"),
    path("mwanzo/", MwanzoView.as_view(), name="api_v1_mwanzo"),
    path("walimu/", WalimuListView.as_view(), name="api_v1_walimu"),
    path("wanafunzi/", WanafunziListView.as_view(), name="api_v1_wanafunzi"),
    path(
        "wanafunzi/<int:mwanafunzi_id>/",
        MwanafunziDetailView.as_view(),
        name="api_v1_mwanafunzi_detail",
    ),
    path("watoro/", WatoroView.as_view(), name="api_v1_watoro"),
    path("malipo/", MalipoListView.as_view(), name="api_v1_malipo"),
    path("aina-malipo/", AinaMalipoListView.as_view(), name="api_v1_aina_malipo"),
    path("mwaka/", MwakaListView.as_view(), name="api_v1_mwaka"),
    path("hamisha/", HamishaPreviewView.as_view(), name="api_v1_hamisha"),
    path("mawasiliano/", MawasilianoListView.as_view(), name="api_v1_mawasiliano"),
    path("ukaguzi/", UkaguziListView.as_view(), name="api_v1_ukaguzi"),
    path("madarasa/", DarasaListView.as_view(), name="api_v1_madarasa"),
    path(
        "madarasa/<int:darasa_id>/wanafunzi/",
        DarasaWanafunziView.as_view(),
        name="api_v1_darasa_wanafunzi",
    ),
    path("mahudhurio/", MahudhurioView.as_view(), name="api_v1_mahudhurio"),
    path("masomo/", SomoListView.as_view(), name="api_v1_masomo"),
    path(
        "masomo/<int:somo_id>/",
        SomoDetailView.as_view(),
        name="api_v1_somo_detail",
    ),
    path("sabaq/", SabaqCreateView.as_view(), name="api_v1_sabaq"),
    path("maendeleo/", MaendeleoCreateView.as_view(), name="api_v1_maendeleo"),
    path("mitihani/", MtihaniListView.as_view(), name="api_v1_mitihani"),
    path(
        "mitihani/<int:mtihani_id>/matokeo/",
        MtihaniMatokeoView.as_view(),
        name="api_v1_matokeo",
    ),
]
