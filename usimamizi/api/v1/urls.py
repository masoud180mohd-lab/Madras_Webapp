from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from usimamizi.api.v1.views import (
    DarasaListView,
    DarasaWanafunziView,
    MahudhurioView,
    MeView,
)

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="api_v1_token"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="api_v1_token_refresh"),
    path("me/", MeView.as_view(), name="api_v1_me"),
    path("madarasa/", DarasaListView.as_view(), name="api_v1_madarasa"),
    path(
        "madarasa/<int:darasa_id>/wanafunzi/",
        DarasaWanafunziView.as_view(),
        name="api_v1_darasa_wanafunzi",
    ),
    path("mahudhurio/", MahudhurioView.as_view(), name="api_v1_mahudhurio"),
]
