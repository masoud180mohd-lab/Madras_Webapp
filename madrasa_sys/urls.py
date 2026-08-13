from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse

from usimamizi.views.media_protected import protected_media


def salamu_ya_api(request):
    """Health ping for uptime checks — not a domain API."""
    return HttpResponse("Muunganisho umefanikiwa!", status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("usimamizi.api.v1.urls")),
    path("madrasa/", include("usimamizi.urls")),
    # Media behind login (dev + prod). Do not expose MEDIA_ROOT as public static.
    re_path(r"^media/(?P<path>.*)$", protected_media, name="protected_media"),
    path("", salamu_ya_api, name="home_ping"),
]

# Token endpoint is opt-in (lab/mobile experiments only). See docs/API.md.
from django.conf import settings  # noqa: E402

if getattr(settings, "ENABLE_TOKEN_AUTH", False):
    from rest_framework.authtoken.views import obtain_auth_token

    urlpatterns.append(
        path("api-token-auth/", obtain_auth_token, name="api_token_auth"),
    )
