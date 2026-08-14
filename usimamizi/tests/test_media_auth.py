import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from usimamizi.models import Mwanafunzi
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo


@HOSTS
class ProtectedMediaTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmpdir = tempfile.mkdtemp(prefix="madrasa_media_")
        cls._media_override = override_settings(MEDIA_ROOT=cls._tmpdir)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._tmpdir, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = create_user_with_cheo("media_user", "Mwalimu Mkuu")
        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
            b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        self.student = Mwanafunzi.objects.create(
            jina_kamili="Mwanafunzi Media",
            picha=SimpleUploadedFile("face.png", png, content_type="image/png"),
        )
        self.media_url = self.student.picha.url

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.media_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("ingia"), response.url)

    def test_jwt_bearer_can_view(self):
        token = self.client.post(
            "/api/v1/auth/token/",
            {"username": "media_user", "password": "pass12345"},
            content_type="application/json",
        )
        self.assertEqual(token.status_code, 200)
        access = token.json()["access"]
        response = self.client.get(
            self.media_url,
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content)[:8], b"\x89PNG\r\n\x1a\n")

    def test_invalid_jwt_is_401(self):
        response = self.client.get(
            self.media_url,
            HTTP_AUTHORIZATION="Bearer not-a-token",
        )
        self.assertEqual(response.status_code, 401)

    def test_logged_in_can_view(self):
        self.client.login(username="media_user", password="pass12345")
        response = self.client.get(self.media_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content)[:8], b"\x89PNG\r\n\x1a\n")

    def test_path_traversal_rejected(self):
        self.client.login(username="media_user", password="pass12345")
        response = self.client.get("/media/../madrasa_sys/settings/base.py")
        self.assertEqual(response.status_code, 404)

    def test_missing_file_404(self):
        self.client.login(username="media_user", password="pass12345")
        response = self.client.get("/media/picha_za_wanafunzi/haipo.png")
        self.assertEqual(response.status_code, 404)
