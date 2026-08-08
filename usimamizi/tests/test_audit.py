from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from usimamizi.models import (
    AinaMalipo,
    Darasa,
    Hudhurio,
    Malipo,
    Mwanafunzi,
    RekodiUkaguzi,
)
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo


@HOSTS
class AuditLogTests(TestCase):
    def setUp(self):
        self.mkuu = create_user_with_cheo("mkuu_audit", "Mwalimu Mkuu")
        self.kawaida = create_user_with_cheo("kawaida_audit", "Mwalimu wa Kawaida")
        self.darasa = Darasa.objects.create(jina="Darasa Audit")
        self.student = Mwanafunzi.objects.create(
            jina_kamili="Audit Student",
            darasa=self.darasa,
        )
        self.aina = AinaMalipo.objects.create(
            jina="Ada Audit",
            kiasi_kinachotakiwa=Decimal("5000"),
        )

    def test_attendance_writes_audit_and_stamps_user(self):
        self.client.login(username="kawaida_audit", password="pass12345")
        response = self.client.post(
            reverse("mahudhurio_darasa", args=[self.darasa.id]),
            {f"yupo_{self.student.id}": "on"},
        )
        self.assertEqual(response.status_code, 302)
        row = Hudhurio.objects.get(mwanafunzi=self.student, tarehe=date.today())
        self.assertEqual(row.iliyorekodiwa_na_id, self.kawaida.id)
        log = RekodiUkaguzi.objects.get(kitendo=RekodiUkaguzi.KITENDO_MAHUDHURIO_KAWAIDA)
        self.assertEqual(log.mtumiaji_id, self.kawaida.id)
        self.assertEqual(log.darasa_id, self.darasa.id)
        self.assertEqual(log.idadi_ya_rekodi, 1)

    def test_payment_writes_audit_and_stamps_user(self):
        self.client.login(username="mkuu_audit", password="pass12345")
        response = self.client.post(
            reverse("weka_malipo", args=[self.student.id, self.aina.id]),
            {"kiasi": "1000", "njia": "Cash", "maelezo": ""},
        )
        self.assertEqual(response.status_code, 302)
        malipo = Malipo.objects.get(mwanafunzi=self.student)
        self.assertEqual(malipo.iliyorekodiwa_na_id, self.mkuu.id)
        log = RekodiUkaguzi.objects.get(kitendo=RekodiUkaguzi.KITENDO_MALIPO)
        self.assertEqual(log.mtumiaji_id, self.mkuu.id)
        self.assertEqual(log.malipo_id, malipo.id)

    def test_ukaguzi_page_for_mkuu(self):
        RekodiUkaguzi.objects.create(
            mtumiaji=self.mkuu,
            kitendo=RekodiUkaguzi.KITENDO_MALIPO,
            maelezo="jaribio",
        )
        self.client.login(username="mkuu_audit", password="pass12345")
        response = self.client.get(reverse("orodha_ukaguzi"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "jaribio")

    def test_ukaguzi_denied_for_kawaida_without_fees(self):
        self.client.login(username="kawaida_audit", password="pass12345")
        response = self.client.get(reverse("orodha_ukaguzi"))
        self.assertEqual(response.status_code, 403)
