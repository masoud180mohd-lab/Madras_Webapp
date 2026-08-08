from django.test import TestCase, override_settings
from django.urls import NoReverseMatch, clear_url_caches, resolve, reverse

from usimamizi.tests.helpers import HOSTS


def _reload_urls():
    """Force URLConf reload after toggling ENABLE_TOKEN_AUTH."""
    from django.conf import settings
    from importlib import reload
    import madrasa_sys.urls as project_urls

    clear_url_caches()
    reload(project_urls)
    settings.ROOT_URLCONF = "madrasa_sys.urls"


@HOSTS
class TokenAuthGateTests(TestCase):
    @override_settings(ENABLE_TOKEN_AUTH=False, ROOT_URLCONF="madrasa_sys.urls")
    def test_token_url_absent_when_disabled(self):
        _reload_urls()
        with self.assertRaises(NoReverseMatch):
            reverse("api_token_auth")
        response = self.client.post(
            "/api-token-auth/",
            {"username": "x", "password": "y"},
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(ENABLE_TOKEN_AUTH=True, ROOT_URLCONF="madrasa_sys.urls")
    def test_token_url_present_when_enabled(self):
        _reload_urls()
        match = resolve("/api-token-auth/")
        self.assertEqual(match.url_name, "api_token_auth")
        # Invalid credentials → 400 from DRF (endpoint is live)
        response = self.client.post(
            "/api-token-auth/",
            {"username": "nope", "password": "nope"},
        )
        self.assertIn(response.status_code, (400, 401))

    def test_health_ping_always_on(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Muunganisho", response.content)
