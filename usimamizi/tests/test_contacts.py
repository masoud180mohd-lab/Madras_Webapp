from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usimamizi.models import Malipo, Mwanafunzi, RekodiSimuMzazi
from usimamizi.permissions import CAP_PARENT_CONTACT, user_has_capability
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo
from usimamizi.whatsapp import build_wa_me_url, normalize_phone_tz, recipient_whatsapp_row

User = get_user_model()


@HOSTS
class ParentContactTests(TestCase):
    def setUp(self):
        self.mkuu = create_user_with_cheo("mkuu_pc", "Mwalimu Mkuu")
        self.kawaida = create_user_with_cheo("kawaida_pc", "Mwalimu wa Kawaida")
        self.office = User.objects.create_user("ofisi_pc", password="pass12345")
        ct = ContentType.objects.get_for_model(Malipo)
        for codename in ("view_malipo", "add_malipo"):
            self.office.user_permissions.add(
                Permission.objects.get(content_type=ct, codename=codename)
            )
        self.student = Mwanafunzi.objects.create(
            jina_kamili="Mwanafunzi Contact",
            jina_la_mzazi="Mzazi Contact",
            namba_ya_simu_mzazi="0777000111",
            uhusiano_wa_mlezi="Baba",
        )

    def test_fees_office_has_parent_contact(self):
        self.assertTrue(user_has_capability(self.office, CAP_PARENT_CONTACT))
        self.assertTrue(user_has_capability(self.mkuu, CAP_PARENT_CONTACT))
        self.assertFalse(user_has_capability(self.kawaida, CAP_PARENT_CONTACT))

    def test_kawaida_denied_mawasiliano(self):
        self.client.login(username="kawaida_pc", password="pass12345")
        self.assertEqual(
            self.client.get(reverse("orodha_mawasiliano")).status_code, 403
        )

    def test_office_list_and_log_call(self):
        self.client.login(username="ofisi_pc", password="pass12345")
        response = self.client.get(reverse("orodha_mawasiliano"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mwanafunzi Contact")
        self.assertContains(response, "0777000111")

        response = self.client.post(
            reverse("mwanafunzi_mawasiliano", args=[self.student.id]),
            {
                "action": "rekodi_simu",
                "namba_iliyopigwa": "0777000111",
                "sababu": RekodiSimuMzazi.SABABU_ADA,
                "matokeo": RekodiSimuMzazi.MATOKEO_AKAAHIDI,
                "maelezo": "Atatoa kesho",
                "tarehe_ya_simu": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            },
        )
        self.assertEqual(response.status_code, 302)
        row = RekodiSimuMzazi.objects.get(mwanafunzi=self.student)
        self.assertEqual(row.matokeo, RekodiSimuMzazi.MATOKEO_AKAAHIDI)
        self.assertEqual(row.iliyorekodiwa_na, self.office)
        self.assertEqual(row.maelezo, "Atatoa kesho")

    def test_update_contact_fields(self):
        self.client.login(username="mkuu_pc", password="pass12345")
        response = self.client.post(
            reverse("mwanafunzi_mawasiliano", args=[self.student.id]),
            {
                "action": "sasisha_mawasiliano",
                "jina_la_mzazi": "Mama Mpya",
                "uhusiano_wa_mlezi": "Mama",
                "namba_ya_simu_mzazi": "0777222333",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertEqual(self.student.jina_la_mzazi, "Mama Mpya")
        self.assertEqual(self.student.namba_ya_simu_mzazi, "0777222333")
        self.assertEqual(self.student.uhusiano_wa_mlezi, "Mama")

    def test_filter_bila_namba(self):
        Mwanafunzi.objects.create(jina_kamili="Bila Namba")
        self.client.login(username="mkuu_pc", password="pass12345")
        response = self.client.get(reverse("orodha_mawasiliano") + "?hali=bila_namba")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bila Namba")
        self.assertNotContains(response, "Mwanafunzi Contact")

    def test_normalize_phone_tz(self):
        self.assertEqual(normalize_phone_tz("0777000111"), "255777000111")
        self.assertEqual(normalize_phone_tz("+255 777 000 111"), "255777000111")
        self.assertEqual(normalize_phone_tz("255777000111"), "255777000111")
        self.assertIsNone(normalize_phone_tz(""))
        self.assertIsNone(normalize_phone_tz("123"))

    def test_wa_me_url_encoding(self):
        url = build_wa_me_url("255777000111", "Habari {jina}")
        self.assertTrue(url.startswith("https://wa.me/255777000111?text="))
        self.assertIn("Habari", url)

    def test_kawaida_denied_whatsapp_campaign(self):
        self.client.login(username="kawaida_pc", password="pass12345")
        self.assertEqual(self.client.get(reverse("tuma_whatsapp")).status_code, 403)

    def test_office_whatsapp_campaign_and_open_logs(self):
        Mwanafunzi.objects.create(jina_kamili="Bila Namba WA")
        bad = Mwanafunzi.objects.create(
            jina_kamili="Namba Mbaya",
            namba_ya_simu_mzazi="12",
        )
        self.client.login(username="ofisi_pc", password="pass12345")
        response = self.client.get(reverse("tuma_whatsapp"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hautumwi kiotomatiki")
        self.assertContains(response, "Mwanafunzi Contact")
        self.assertContains(response, "Fungua WhatsApp")
        self.assertNotContains(response, "Bila Namba WA")
        row_bad = recipient_whatsapp_row(bad, "Salamu {jina}")
        self.assertFalse(row_bad["ina_namba_sahihi"])
        self.assertIsNone(row_bad["wa_url"])

        response = self.client.get(
            reverse("fungua_whatsapp", args=[self.student.id]) + "?kigezo=ada",
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("https://wa.me/255777000111"))
        log = RekodiSimuMzazi.objects.filter(
            mwanafunzi=self.student,
            sababu=RekodiSimuMzazi.SABABU_WHATSAPP,
        ).latest("tarehe_ya_simu")
        self.assertEqual(log.matokeo, RekodiSimuMzazi.MATOKEO_IMEANZISHWA)
        self.assertEqual(log.iliyorekodiwa_na, self.office)

    def test_detail_shows_whatsapp_when_valid(self):
        self.client.login(username="mkuu_pc", password="pass12345")
        response = self.client.get(
            reverse("mwanafunzi_mawasiliano", args=[self.student.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "WhatsApp")
        self.assertContains(response, reverse("fungua_whatsapp", args=[self.student.id]))
