from django.contrib.auth import get_user
from django.test import TestCase
from django.urls import reverse

from usimamizi.tests.helpers import HOSTS, create_user_with_cheo


@HOSTS
class AuthFlowTests(TestCase):
    def setUp(self):
        self.user = create_user_with_cheo("mkuu_auth", "Mwalimu Mkuu")

    def test_login_success_redirects_home(self):
        response = self.client.post(
            reverse("ingia"),
            {"username": "mkuu_auth", "password": "pass12345"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("mwanzo"))
        self.assertTrue(get_user(self.client).is_authenticated)

    def test_login_failure_stays_on_form(self):
        response = self.client.post(
            reverse("ingia"),
            {"username": "mkuu_auth", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_logout_clears_session(self):
        self.client.login(username="mkuu_auth", password="pass12345")
        response = self.client.get(reverse("toka"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("ingia"))
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_unauthenticated_home_redirects_to_login(self):
        response = self.client.get(reverse("mwanzo"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("ingia"), response.url)
