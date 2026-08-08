from django.test import TestCase
from django.urls import reverse

from usimamizi.academic import get_active_muhula, get_active_mwaka, set_active_muhula
from usimamizi.forms import MsetoMtihaniForm
from usimamizi.models import Darasa, MsetoMtihani, Muhula, MwakaWaMasomo
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo


@HOSTS
class AcademicYearTests(TestCase):
    def setUp(self):
        # Migration may seed current calendar year — clear for deterministic tests.
        MwakaWaMasomo.objects.all().delete()
        self.mkuu = create_user_with_cheo("mkuu_mwaka", "Mwalimu Mkuu")
        self.kawaida = create_user_with_cheo("kawaida_mwaka", "Mwalimu wa Kawaida")
        self.mwaka = MwakaWaMasomo.objects.create(
            jina="2026/2027",
            mwaka_kuanzia=2026,
            mwaka_kuisha=2027,
            ni_hai=True,
        )
        self.muhula1 = Muhula.objects.create(
            mwaka=self.mwaka, namba=1, jina="Muhula wa 1", ni_hai=True
        )
        self.muhula2 = Muhula.objects.create(
            mwaka=self.mwaka, namba=2, jina="Muhula wa 2", ni_hai=False
        )
        self.darasa = Darasa.objects.create(jina="Darasa Mwaka")

    def test_only_one_active_muhula(self):
        set_active_muhula(self.muhula2)
        self.muhula1.refresh_from_db()
        self.muhula2.refresh_from_db()
        self.assertFalse(self.muhula1.ni_hai)
        self.assertTrue(self.muhula2.ni_hai)
        self.assertEqual(get_active_muhula(), self.muhula2)

    def test_mseto_links_to_muhula(self):
        mseto = MsetoMtihani.objects.create(
            darasa=self.darasa,
            muhula=self.muhula1,
            jina="Mseto jaribio",
        )
        self.assertEqual(mseto.muhula, self.muhula1)
        self.assertEqual(mseto.muhula.mwaka, self.mwaka)

    def test_mseto_form_prefills_active_muhula(self):
        form = MsetoMtihaniForm()
        self.assertEqual(form.initial.get("muhula"), self.muhula1.pk)
        self.assertIn("Muhula wa 1", form.initial.get("jina", ""))

    def test_page_allowed_for_mkuu(self):
        self.client.login(username="mkuu_mwaka", password="pass12345")
        response = self.client.get(reverse("mwaka_masomo"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mwaka na muhula")
        self.assertContains(response, "2026/2027")

    def test_page_denied_for_kawaida(self):
        self.client.login(username="kawaida_mwaka", password="pass12345")
        response = self.client.get(reverse("mwaka_masomo"))
        self.assertEqual(response.status_code, 403)

    def test_select_active_muhula_via_post(self):
        self.client.login(username="mkuu_mwaka", password="pass12345")
        response = self.client.post(
            reverse("mwaka_masomo"),
            {"action": "weka_muhula_hai", "muhula_id": self.muhula2.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_active_muhula().id, self.muhula2.id)
        self.assertTrue(get_active_mwaka().ni_hai)

    def test_create_mwaka_via_post(self):
        self.client.login(username="mkuu_mwaka", password="pass12345")
        response = self.client.post(
            reverse("mwaka_masomo"),
            {
                "action": "unda_mwaka",
                "jina": "2027/2028",
                "mwaka_kuanzia": "2027",
                "mwaka_kuisha": "2028",
                "ni_hai": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(MwakaWaMasomo.objects.filter(jina="2027/2028", ni_hai=True).exists())
        self.mwaka.refresh_from_db()
        self.assertFalse(self.mwaka.ni_hai)
