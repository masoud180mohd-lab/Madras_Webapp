from django.test import TestCase
from django.urls import reverse

from usimamizi.models import Mwanafunzi
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo


@HOSTS
class StudentArchiveTests(TestCase):
    def setUp(self):
        self.mkuu = create_user_with_cheo("mkuu_arch", "Mwalimu Mkuu")
        self.kawaida = create_user_with_cheo("kawaida_arch", "Mwalimu wa Kawaida")
        self.student = Mwanafunzi.objects.create(jina_kamili="Archive Student")

    def test_archive_hides_from_active_list(self):
        self.client.login(username="mkuu_arch", password="pass12345")
        response = self.client.post(
            reverse("hifadhi_mwanafunzi", args=[self.student.id]),
            {"sababu": "Amehamia"},
        )
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertTrue(self.student.amehifadhiwa)
        self.assertEqual(self.student.sababu_ya_kuhifadhiwa, "Amehamia")

        active = self.client.get(reverse("orodha_wanafunzi"))
        active_ids = [row.id for row in active.context["page_obj"]]
        self.assertNotIn(self.student.id, active_ids)
        archived = self.client.get(reverse("orodha_wanafunzi") + "?hali=hifadhiwa")
        archived_ids = [row.id for row in archived.context["page_obj"]]
        self.assertIn(self.student.id, archived_ids)

    def test_restore_returns_to_active_list(self):
        self.student.archive(sababu="temp")
        self.client.login(username="mkuu_arch", password="pass12345")
        self.client.post(reverse("rudisha_mwanafunzi", args=[self.student.id]))
        self.student.refresh_from_db()
        self.assertFalse(self.student.amehifadhiwa)
        active = self.client.get(reverse("orodha_wanafunzi"))
        self.assertContains(active, "Archive Student")

    def test_kawaida_cannot_archive(self):
        self.client.login(username="kawaida_arch", password="pass12345")
        response = self.client.post(
            reverse("hifadhi_mwanafunzi", args=[self.student.id])
        )
        self.assertEqual(response.status_code, 403)
        self.student.refresh_from_db()
        self.assertFalse(self.student.amehifadhiwa)

    def test_dashboard_counts_active_only(self):
        from usimamizi.dashboard import build_dashboard_context

        Mwanafunzi.objects.create(jina_kamili="Active Other")
        self.student.archive()
        ctx = build_dashboard_context(self.mkuu)
        wanafunzi = next(m for m in ctx["vipimo"] if m["label"] == "Wanafunzi")
        self.assertEqual(wanafunzi["value"], 1)

    def test_profile_still_readable_when_archived(self):
        self.student.archive()
        self.client.login(username="kawaida_arch", password="pass12345")
        response = self.client.get(
            reverse("mwanafunzi_profile", args=[self.student.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amehifadhiwa")
