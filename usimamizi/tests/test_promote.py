from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from usimamizi.models import Darasa, Mwanafunzi, RekodiUkaguzi
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo


@HOSTS
class PromoteClassTests(TestCase):
    def setUp(self):
        self.mkuu = create_user_with_cheo("mkuu_prom", "Mwalimu Mkuu")
        self.kawaida = create_user_with_cheo("kawaida_prom", "Mwalimu wa Kawaida")
        self.office = User.objects.create_user("ofisi_prom", password="pass12345")
        for codename in ("add_mwanafunzi", "change_mwanafunzi", "view_mwanafunzi"):
            self.office.user_permissions.add(
                Permission.objects.get(codename=codename, content_type__app_label="usimamizi")
            )
        self.a = Darasa.objects.create(jina="Darasa A Prom")
        self.b = Darasa.objects.create(jina="Darasa B Prom")
        self.s1 = Mwanafunzi.objects.create(jina_kamili="Prom Student One", darasa=self.a)
        self.s2 = Mwanafunzi.objects.create(jina_kamili="Prom Student Two", darasa=self.a)
        self.archived = Mwanafunzi.objects.create(
            jina_kamili="Prom Archived",
            darasa=self.a,
            amehifadhiwa=True,
        )

    def test_kawaida_and_office_denied(self):
        self.client.login(username="kawaida_prom", password="pass12345")
        self.assertEqual(self.client.get(reverse("hamisha_darasa")).status_code, 403)
        self.client.logout()
        self.client.login(username="ofisi_prom", password="pass12345")
        self.assertEqual(self.client.get(reverse("hamisha_darasa")).status_code, 403)

    def test_same_class_rejected(self):
        self.client.login(username="mkuu_prom", password="pass12345")
        response = self.client.post(
            reverse("hamisha_darasa"),
            {
                "action": "hakiki",
                "kutoka": self.a.id,
                "kwenda": self.a.id,
                "wanafunzi": [self.s1.id],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.darasa_id, self.a.id)

    def test_mkuu_promotes_with_confirm_and_audit(self):
        self.client.login(username="mkuu_prom", password="pass12345")
        list_page = self.client.get(reverse("hamisha_darasa") + f"?kutoka={self.a.id}")
        self.assertEqual(list_page.status_code, 200)
        self.assertContains(list_page, "Prom Student One")
        self.assertNotContains(list_page, "Prom Archived")

        confirm = self.client.post(
            reverse("hamisha_darasa"),
            {
                "action": "hakiki",
                "kutoka": self.a.id,
                "kwenda": self.b.id,
                "wanafunzi": [self.s1.id, self.s2.id],
                "maezo": "Mwisho wa mwaka",
            },
        )
        self.assertEqual(confirm.status_code, 200)
        self.assertContains(confirm, "Thibitisha uhamisho")

        done = self.client.post(
            reverse("hamisha_darasa"),
            {
                "action": "thibitisha",
                "kutoka": self.a.id,
                "kwenda": self.b.id,
                "wanafunzi": [self.s1.id, self.s2.id],
                "maezo": "Mwisho wa mwaka",
            },
        )
        self.assertEqual(done.status_code, 302)
        self.s1.refresh_from_db()
        self.s2.refresh_from_db()
        self.archived.refresh_from_db()
        self.assertEqual(self.s1.darasa_id, self.b.id)
        self.assertEqual(self.s2.darasa_id, self.b.id)
        self.assertEqual(self.archived.darasa_id, self.a.id)

        log = RekodiUkaguzi.objects.filter(
            kitendo=RekodiUkaguzi.KITENDO_HAMISHA_DARASA
        ).latest("tarehe_ya_kitendo")
        self.assertEqual(log.idadi_ya_rekodi, 2)
        self.assertIn("Darasa A Prom", log.maelezo)
        self.assertIn("Darasa B Prom", log.maelezo)
        self.assertIn("Mwisho wa mwaka", log.maelezo)
