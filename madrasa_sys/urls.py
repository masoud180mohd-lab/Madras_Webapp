from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


def salamu_ya_api(request):
    """Health ping for uptime checks — not a domain API."""
    return HttpResponse("Muunganisho umefanikiwa!", status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("madrasa/", include("usimamizi.urls")),
    path("", salamu_ya_api, name="home_ping"),
]

# Token endpoint is opt-in (lab/mobile experiments only). See docs/API.md.
if getattr(settings, "ENABLE_TOKEN_AUTH", False):
    from rest_framework.authtoken.views import obtain_auth_token

    urlpatterns.append(
        path("api-token-auth/", obtain_auth_token, name="api_token_auth"),
    )

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
