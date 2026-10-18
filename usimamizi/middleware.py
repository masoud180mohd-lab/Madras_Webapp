"""
Prevent browser back-button from showing authenticated pages after logout.

Chrome/Edge keep a history snapshot (bfcache). Without Cache-Control: no-store,
← back can show the previous page even though the session was cleared.
"""


from django.http import HttpResponse


class RenderHealthCheckMiddleware:
    """
    Respond 200 OK to Render's internal health-check probe (``User-Agent: Render/1.0``
    against ``/``) before ``SecurityMiddleware`` / ``CommonMiddleware`` calls
    ``request.get_host()``, since Render probes via internal ``10.x.x.x`` container IPs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/" and request.META.get("HTTP_USER_AGENT", "").startswith("Render/"):
            return HttpResponse("Muunganisho umefanikiwa!", status=200)
        return self.get_response(request)


class NoCacheAuthenticatedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response

