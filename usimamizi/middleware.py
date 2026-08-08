"""
Prevent browser back-button from showing authenticated pages after logout.

Chrome/Edge keep a history snapshot (bfcache). Without Cache-Control: no-store,
← back can show the previous page even though the session was cleared.
"""


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
