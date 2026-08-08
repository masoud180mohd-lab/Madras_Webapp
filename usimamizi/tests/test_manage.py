from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from usimamizi.models import AinaMalipo, Darasa, Malipo, Mwalimu, MwakaWaMasomo, Mwanafunzi
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo

User = get_user_model()


@HOSTS
class ManageCrudTests(TestCase):
    def setUp(self):
        self.mkuu = create_user_with_cheo("mkuu_crud", "Mwalimu Mkuu")
        self.kawaida = create_user_with_cheo("kawaida_crud", "Mwalimu wa Kawaida")
        self.darasa = Darasa.objects.create(jina="Darasa CRUD")
        self.mwaka = MwakaWaMasomo.objects.create(
            jina="2025/2026",
            mwaka_kuanzia=2025,
            mwaka_kuisha=2026,
            ni_hai=True,
        )
        self.aina = AinaMalipo.objects.create(
            jina="Ada ya Mwezi",
            mwaka=self.mwaka,
            mwezi=4,
            kiasi_kinachotakiwa=Decimal("10000.00"),
        )

    def test_kawaida_denied_manage_pages(self):
        self.client.login(username="kawaida_crud", password="pass12345")
        for name, kwargs in [
            ("ongeza_darasa", {}),
            ("hariri_darasa", {"darasa_id": self.darasa.id}),
            ("ongeza_mwalimu", {}),
            ("orodha_aina_malipo", {}),
            ("ongeza_aina_malipo", {}),
        ]:
            response = self.client.get(reverse(name, kwargs=kwargs))
            self.assertEqual(response.status_code, 403, name)

    def test_mkuu_create_and_edit_darasa(self):
        self.client.login(username="mkuu_crud", password="pass12345")
        response = self.client.post(
            reverse("ongeza_darasa"),
            {"jina": "Darasa Jipya", "maelezo": "Maelezo"},
        )
        self.assertEqual(response.status_code, 302)
        darasa = Darasa.objects.get(jina="Darasa Jipya")
        response = self.client.post(
            reverse("hariri_darasa", kwargs={"darasa_id": darasa.id}),
            {"jina": "Darasa Lililosasishwa", "maelezo": ""},
        )
        self.assertEqual(response.status_code, 302)
        darasa.refresh_from_db()
        self.assertEqual(darasa.jina, "Darasa Lililosasishwa")

    def test_cannot_delete_darasa_with_students(self):
        Mwanafunzi.objects.create(
            jina_kamili="Mwanafunzi CRUD",
            jinsia="M",
            darasa=self.darasa,
        )
        self.client.login(username="mkuu_crud", password="pass12345")
        response = self.client.post(
            reverse("futa_darasa", kwargs={"darasa_id": self.darasa.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Darasa.objects.filter(id=self.darasa.id).exists())

    def test_delete_empty_darasa(self):
        empty = Darasa.objects.create(jina="Tupu")
        self.client.login(username="mkuu_crud", password="pass12345")
        response = self.client.post(
            reverse("futa_darasa", kwargs={"darasa_id": empty.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Darasa.objects.filter(id=empty.id).exists())

    def test_mkuu_create_mwalimu(self):
        self.client.login(username="mkuu_crud", password="pass12345")
        response = self.client.post(
            reverse("ongeza_mwalimu"),
            {
                "username": "mwalimu_mpya",
                "password": "Nenosiri_salama_99",
                "first_name": "Ali",
                "last_name": "Hassan",
                "cheo": "Mwalimu wa Kawaida",
                "namba_ya_simu": "0777123456",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="mwalimu_mpya")
        self.assertTrue(hasattr(user, "mwalimu"))
        self.assertEqual(user.mwalimu.cheo, "Mwalimu wa Kawaida")

    def test_edit_mwalimu_can_deactivate(self):
        target = create_user_with_cheo("target_mw", "Mwalimu wa Kawaida")
        mwalimu = target.mwalimu
        self.client.login(username="mkuu_crud", password="pass12345")
        response = self.client.post(
            reverse("hariri_mwalimu", kwargs={"mwalimu_id": mwalimu.id}),
            {
                "first_name": "Target",
                "last_name": "Mwalimu",
                "cheo": "Jaji",
                "namba_ya_simu": "",
                # is_active unchecked => inactive
            },
        )
        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        mwalimu.refresh_from_db()
        self.assertFalse(target.is_active)
        self.assertEqual(mwalimu.cheo, "Jaji")

    def test_aina_malipo_crud_and_delete_guard(self):
        self.client.login(username="mkuu_crud", password="pass12345")
        response = self.client.get(reverse("orodha_aina_malipo"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ada ya Mwezi")

        response = self.client.post(
            reverse("ongeza_aina_malipo"),
            {
                "mwaka": self.mwaka.id,
                "mwezi": "",
                "jina": "Mchango Mtihani",
                "kiasi_kinachotakiwa": "5000.00",
                "maelezo": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        aina = AinaMalipo.objects.get(jina="Mchango Mtihani")
        self.assertEqual(aina.mwaka_id, self.mwaka.id)

        mwanafunzi = Mwanafunzi.objects.create(
            jina_kamili="Mlipaji",
            jinsia="M",
            darasa=self.darasa,
        )
        Malipo.objects.create(
            mwanafunzi=mwanafunzi,
            aina_ya_malipo=aina,
            kiasi_kilicholipwa=Decimal("5000.00"),
            mpokeaji=self.mkuu.mwalimu,
        )
        response = self.client.post(
            reverse("futa_aina_malipo", kwargs={"aina_id": aina.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AinaMalipo.objects.filter(id=aina.id).exists())

        unused = AinaMalipo.objects.create(
            jina="Isiyotumika",
            mwaka=self.mwaka,
            kiasi_kinachotakiwa=Decimal("1000"),
        )
        response = self.client.post(
            reverse("futa_aina_malipo", kwargs={"aina_id": unused.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AinaMalipo.objects.filter(id=unused.id).exists())

    def test_april_fee_types_distinct_by_year(self):
        other = MwakaWaMasomo.objects.create(
            jina="2026/2027",
            mwaka_kuanzia=2026,
            mwaka_kuisha=2027,
            ni_hai=False,
        )
        a2 = AinaMalipo.objects.create(
            jina="Ada · Aprili",
            mwaka=other,
            mwezi=4,
            kiasi_kinachotakiwa=Decimal("12000"),
        )
        self.assertIn("2025/2026", self.aina.lebo_kamili)
        self.assertIn("2026/2027", a2.lebo_kamili)
        self.assertNotEqual(self.aina.lebo_kamili, a2.lebo_kamili)

        self.client.login(username="mkuu_crud", password="pass12345")
        dup = self.client.post(
            reverse("ongeza_aina_malipo"),
            {
                "mwaka": self.mwaka.id,
                "mwezi": "4",
                "jina": "",
                "kiasi_kinachotakiwa": "10000",
                "maelezo": "",
            },
        )
        self.assertEqual(dup.status_code, 200)
        self.assertContains(dup, "tayari ipo")
