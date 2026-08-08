from django.test import TestCase
from django.urls import reverse

from usimamizi.tests.helpers import HOSTS, create_user_with_cheo


@HOSTS
class NoCacheMiddlewareTests(TestCase):
    def setUp(self):
        create_user_with_cheo("mkuu_cache", "Mwalimu Mkuu")

    def test_authenticated_response_has_no_store(self):
        self.client.login(username="mkuu_cache", password="pass12345")
        response = self.client.get(reverse("mwanzo"))
        self.assertEqual(response.status_code, 200)
        cache_control = response.get("Cache-Control", "")
        self.assertIn("no-store", cache_control)
        self.assertEqual(response.get("Pragma"), "no-cache")
        self.assertEqual(response.get("Expires"), "0")

    def test_anonymous_login_page_not_forced_no_store(self):
        response = self.client.get(reverse("ingia"))
        self.assertEqual(response.status_code, 200)
        cache_control = response.get("Cache-Control", "")
        self.assertNotIn("no-store", cache_control)
