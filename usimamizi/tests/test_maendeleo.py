from django.test import TestCase
from django.urls import reverse

from usimamizi.models import Darasa, Mwanafunzi, RekodiMaendeleoMchana, Somo
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo


@HOSTS
class MaendeleoMchanaTests(TestCase):
    def setUp(self):
        self.mkuu = create_user_with_cheo("mkuu_mm", "Mwalimu Mkuu")
        self.kawaida = create_user_with_cheo("kawaida_mm", "Mwalimu wa Kawaida")
        self.jaji = create_user_with_cheo("jaji_mm", "Jaji")
        self.darasa = Darasa.objects.create(jina="Darasa MM")
        self.somo = Somo.objects.create(
            jina="Fiqhi",
            ni_la_hifdhu=False,
            darasa=self.darasa,
            mwalimu=self.kawaida.mwalimu,
        )
        self.hifdhu = Somo.objects.create(
            jina="Hifdhu MM",
            ni_la_hifdhu=True,
            darasa=self.darasa,
        )
        self.student = Mwanafunzi.objects.create(
            jina_kamili="Mwanafunzi MM",
            darasa=self.darasa,
        )

    def test_list_students_for_day_subject(self):
        self.client.login(username="kawaida_mm", password="pass12345")
        response = self.client.get(
            reverse("wanafunzi_maendeleo_mchana", args=[self.somo.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mwanafunzi MM")
        self.assertContains(response, "Fiqhi")

    def test_hifdhu_subject_redirects_to_sabaq_list(self):
        self.client.login(username="kawaida_mm", password="pass12345")
        response = self.client.get(
            reverse("wanafunzi_maendeleo_mchana", args=[self.hifdhu.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("wanafunzi_hifdhu", args=[self.hifdhu.id]),
            response.url,
        )

    def test_record_progress(self):
        self.client.login(username="kawaida_mm", password="pass12345")
        response = self.client.post(
            reverse(
                "rekodi_maendeleo_mchana",
                args=[self.student.id, self.somo.id],
            ),
            {
                "mada_iliyosomwa": "Mlango wa Udhu",
                "ukurasa_au_aya": "12-15",
                "hali": RekodiMaendeleoMchana.HALI_AMEELEWA,
                "maoni": "Vizuri",
            },
        )
        self.assertEqual(response.status_code, 302)
        row = RekodiMaendeleoMchana.objects.get(mwanafunzi=self.student)
        self.assertEqual(row.mada_iliyosomwa, "Mlango wa Udhu")
        self.assertEqual(row.mwalimu, self.kawaida.mwalimu)
        self.assertEqual(row.somo, self.somo)

    def test_jaji_cannot_record(self):
        self.client.login(username="jaji_mm", password="pass12345")
        response = self.client.get(
            reverse(
                "rekodi_maendeleo_mchana",
                args=[self.student.id, self.somo.id],
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_report_view(self):
        RekodiMaendeleoMchana.objects.create(
            mwanafunzi=self.student,
            somo=self.somo,
            mwalimu=self.kawaida.mwalimu,
            mada_iliyosomwa="Salah",
            hali=RekodiMaendeleoMchana.HALI_HAJAELEWA,
        )
        self.client.login(username="mkuu_mm", password="pass12345")
        response = self.client.get(
            reverse("ripoti_maendeleo_mchana", args=[self.student.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Salah")
        self.assertContains(response, "Fiqhi")
