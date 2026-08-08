from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from usimamizi.models import Malipo, Mwanafunzi, RekodiHifdhu
from usimamizi.permissions import (
    CAP_ATTENDANCE,
    CAP_EXAMS,
    CAP_FEES,
    CAP_MANAGE_STUDENTS,
    CAP_SABAQ,
    user_has_capability,
)
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo


@HOSTS
class AuthZRoleMatrixTests(TestCase):
    def setUp(self):
        self.student = Mwanafunzi.objects.create(jina_kamili="AuthZ Student")

        self.mkuu_user = create_user_with_cheo("mkuu", "Mwalimu Mkuu")
        self.kawaida_user = create_user_with_cheo("kawaida", "Mwalimu wa Kawaida")
        self.jaji_user = create_user_with_cheo("jaji", "Jaji")

        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.office_user = User.objects.create_user("ofisi", password="pass12345")
        ct = ContentType.objects.get_for_model(Malipo)
        for codename in ("view_malipo", "add_malipo"):
            perm = Permission.objects.get(content_type=ct, codename=codename)
            self.office_user.user_permissions.add(perm)

        self.bare_user = User.objects.create_user("bare", password="pass12345")

    def test_mkuu_has_fees_and_manage_students(self):
        self.assertTrue(user_has_capability(self.mkuu_user, CAP_FEES))
        self.assertTrue(user_has_capability(self.mkuu_user, CAP_MANAGE_STUDENTS))

    def test_kawaida_denied_fees_allowed_attendance(self):
        self.assertFalse(user_has_capability(self.kawaida_user, CAP_FEES))
        self.assertTrue(user_has_capability(self.kawaida_user, CAP_ATTENDANCE))
        self.assertTrue(user_has_capability(self.kawaida_user, CAP_SABAQ))
        self.assertTrue(user_has_capability(self.kawaida_user, CAP_EXAMS))

    def test_jaji_exams_not_fees_or_sabaq(self):
        self.assertTrue(user_has_capability(self.jaji_user, CAP_EXAMS))
        self.assertFalse(user_has_capability(self.jaji_user, CAP_FEES))
        self.assertFalse(user_has_capability(self.jaji_user, CAP_SABAQ))
        self.assertFalse(user_has_capability(self.jaji_user, CAP_ATTENDANCE))

    def test_office_fees_via_django_perms(self):
        self.assertTrue(user_has_capability(self.office_user, CAP_FEES))
        self.assertFalse(user_has_capability(self.office_user, CAP_ATTENDANCE))

    def test_bare_user_denied_sensitive_reads(self):
        self.client.login(username="bare", password="pass12345")
        self.assertEqual(self.client.get("/madrasa/malipo/").status_code, 403)
        self.assertEqual(
            self.client.get(f"/madrasa/mwanafunzi/profile/{self.student.id}/").status_code,
            403,
        )

    def test_kawaida_can_view_student_but_not_fees(self):
        self.client.login(username="kawaida", password="pass12345")
        self.assertEqual(
            self.client.get(f"/madrasa/mwanafunzi/profile/{self.student.id}/").status_code,
            200,
        )
        self.assertEqual(self.client.get("/madrasa/malipo/").status_code, 403)

    def test_jaji_can_view_matokeo_path_capability(self):
        self.assertTrue(user_has_capability(self.jaji_user, CAP_EXAMS))

    def test_sabaq_without_mwalimu_redirects(self):
        ct = ContentType.objects.get_for_model(RekodiHifdhu)
        perm = Permission.objects.get(content_type=ct, codename="add_rekodihifdhu")
        self.office_user.user_permissions.add(perm)

        self.client.login(username="ofisi", password="pass12345")
        response = self.client.get(
            f"/madrasa/rekodi_sabaq/{self.student.id}/Darasa/",
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/madrasa/")
