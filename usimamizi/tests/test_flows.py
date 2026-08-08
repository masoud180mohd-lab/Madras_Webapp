from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from usimamizi.models import (
    AinaMalipo,
    Darasa,
    Hudhurio,
    Malipo,
    Matokeo,
    Mtihani,
    Mwanafunzi,
    Somo,
)
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo
from usimamizi.utils import hesabu_daraja


@HOSTS
class AttendanceFlowTests(TestCase):
    def setUp(self):
        create_user_with_cheo("mkuu_att", "Mwalimu Mkuu")
        self.darasa = Darasa.objects.create(jina="Darasa Attendance")
        self.student = Mwanafunzi.objects.create(
            jina_kamili="Attendance Flow Student",
            darasa=self.darasa,
        )
        self.url = reverse("mahudhurio_darasa", args=[self.darasa.id])

    def test_post_records_attendance_once(self):
        self.client.login(username="mkuu_att", password="pass12345")
        response = self.client.post(
            self.url,
            {f"yupo_{self.student.id}": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Hudhurio.objects.filter(
                mwanafunzi=self.student,
                tarehe=date.today(),
                aina_ya_rekodi="Kawaida",
            ).count(),
            1,
        )

    def test_second_post_same_day_blocked(self):
        self.client.login(username="mkuu_att", password="pass12345")
        self.client.post(self.url, {f"yupo_{self.student.id}": "on"})
        before = Hudhurio.objects.filter(mwanafunzi=self.student).count()
        response = self.client.post(self.url, {f"yupo_{self.student.id}": "on"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Hudhurio.objects.filter(mwanafunzi=self.student).count(), before)


@HOSTS
class MarksFlowTests(TestCase):
    def setUp(self):
        create_user_with_cheo("mkuu_marks", "Mwalimu Mkuu")
        self.darasa = Darasa.objects.create(jina="Darasa Marks")
        self.somo = Somo.objects.create(jina="Fiqhi Marks", darasa=self.darasa)
        self.mtihani = Mtihani.objects.create(
            somo=self.somo,
            jina_la_mtihani="Mtihani Flow",
            tarehe=date(2026, 7, 1),
        )
        self.student = Mwanafunzi.objects.create(
            jina_kamili="Marks Flow Student",
            darasa=self.darasa,
        )
        self.url = reverse("weka_maksi", args=[self.mtihani.id])

    def test_post_saves_marks(self):
        self.client.login(username="mkuu_marks", password="pass12345")
        response = self.client.post(
            self.url,
            {f"maksi_{self.student.id}": "75"},
        )
        self.assertEqual(response.status_code, 302)
        row = Matokeo.objects.get(mtihani=self.mtihani, mwanafunzi=self.student)
        self.assertEqual(row.maksi, 75)

    def test_post_updates_existing_marks(self):
        Matokeo.objects.create(
            mtihani=self.mtihani, mwanafunzi=self.student, maksi=40
        )
        self.client.login(username="mkuu_marks", password="pass12345")
        self.client.post(self.url, {f"maksi_{self.student.id}": "90"})
        self.assertEqual(
            Matokeo.objects.filter(mtihani=self.mtihani, mwanafunzi=self.student).count(),
            1,
        )
        self.assertEqual(
            Matokeo.objects.get(mtihani=self.mtihani, mwanafunzi=self.student).maksi,
            90,
        )

    def test_out_of_range_rejected(self):
        self.client.login(username="mkuu_marks", password="pass12345")
        self.client.post(self.url, {f"maksi_{self.student.id}": "150"})
        self.assertFalse(
            Matokeo.objects.filter(mtihani=self.mtihani, mwanafunzi=self.student).exists()
        )


@HOSTS
class FeesFlowTests(TestCase):
    def setUp(self):
        create_user_with_cheo("mkuu_fees", "Mwalimu Mkuu")
        create_user_with_cheo("kawaida_fees", "Mwalimu wa Kawaida")
        self.student = Mwanafunzi.objects.create(jina_kamili="Fees Flow Student")
        self.aina = AinaMalipo.objects.create(
            jina="Ada Test",
            kiasi_kinachotakiwa=Decimal("10000.00"),
        )
        self.url = reverse("weka_malipo", args=[self.student.id, self.aina.id])

    def test_mkuu_records_payment(self):
        self.client.login(username="mkuu_fees", password="pass12345")
        response = self.client.post(
            self.url,
            {"kiasi": "2500", "njia": "Cash", "maelezo": "Sehemu"},
        )
        self.assertEqual(response.status_code, 302)
        payment = Malipo.objects.get(mwanafunzi=self.student, aina_ya_malipo=self.aina)
        self.assertEqual(payment.kiasi_kilicholipwa, Decimal("2500.00"))
        self.assertEqual(payment.njia_ya_malipo, "Cash")

    def test_overpay_rejected(self):
        self.client.login(username="mkuu_fees", password="pass12345")
        self.client.post(
            self.url,
            {"kiasi": "15000", "njia": "Cash", "maelezo": ""},
        )
        self.assertFalse(
            Malipo.objects.filter(mwanafunzi=self.student, aina_ya_malipo=self.aina).exists()
        )

    def test_kawaida_denied_fee_write(self):
        self.client.login(username="kawaida_fees", password="pass12345")
        response = self.client.post(
            self.url,
            {"kiasi": "1000", "njia": "Cash", "maelezo": ""},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Malipo.objects.filter(mwanafunzi=self.student).exists())


class HesabuDarajaTests(TestCase):
    def test_grade_boundaries(self):
        self.assertEqual(hesabu_daraja(81)[0], "A")
        self.assertEqual(hesabu_daraja(61)[0], "B")
        self.assertEqual(hesabu_daraja(41)[0], "C")
        self.assertEqual(hesabu_daraja(31)[0], "D")
        self.assertEqual(hesabu_daraja(30)[0], "F")
