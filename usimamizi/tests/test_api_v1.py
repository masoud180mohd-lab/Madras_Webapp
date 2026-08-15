from datetime import date

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from usimamizi.models import (
    Darasa,
    Hudhurio,
    Matokeo,
    Mtihani,
    Malipo,
    Mwanafunzi,
    RekodiHifdhu,
    RekodiMaendeleoMchana,
    Somo,
)
from usimamizi.permissions import (
    CAP_ATTENDANCE,
    CAP_EXAMS,
    CAP_FEES,
    CAP_VIEW_DIRECTORY,
    CAP_VIEW_STUDENTS,
)
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo

NO_THROTTLE = override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)


@HOSTS
@NO_THROTTLE
class ApiV1Tests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.darasa = Darasa.objects.create(jina="Darasa la Kwanza")
        self.s1 = Mwanafunzi.objects.create(
            jina_kamili="API Student A",
            darasa=self.darasa,
            namba_ya_simu_mzazi="0771111111",
        )
        self.s2 = Mwanafunzi.objects.create(
            jina_kamili="API Student B",
            darasa=self.darasa,
        )
        self.archived = Mwanafunzi.objects.create(
            jina_kamili="API Student Archived",
            darasa=self.darasa,
        )
        self.archived.archive(sababu="test")

        self.mkuu = create_user_with_cheo("api_mkuu", "Mwalimu Mkuu")
        self.kawaida = create_user_with_cheo("api_kawaida", "Mwalimu wa Kawaida")
        self.jaji = create_user_with_cheo("api_jaji", "Jaji")

        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.office = User.objects.create_user("api_ofisi", password="pass12345")
        ct = ContentType.objects.get_for_model(Malipo)
        for codename in ("view_malipo", "add_malipo"):
            perm = Permission.objects.get(content_type=ct, codename=codename)
            self.office.user_permissions.add(perm)
        self.bare = User.objects.create_user("api_bare", password="pass12345")

    def _token(self, username, password="pass12345"):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        return response.data["access"]

    def _auth(self, username):
        token = self._token(username)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _roll_payload(self, *, yupo_map=None):
        yupo_map = yupo_map or {}
        return {
            "darasa": self.darasa.id,
            "tarehe": date.today().isoformat(),
            "aina_ya_rekodi": "Kawaida",
            "rekodi": [
                {
                    "mwanafunzi": self.s1.id,
                    "yupo": yupo_map.get(self.s1.id, True),
                    "sababu_kama_hayupo": "" if yupo_map.get(self.s1.id, True) else "mgonjwa",
                },
                {
                    "mwanafunzi": self.s2.id,
                    "yupo": yupo_map.get(self.s2.id, True),
                    "sababu_kama_hayupo": "",
                },
            ],
        }

    def test_unauthenticated_me_is_401(self):
        response = self.client.get("/api/v1/me/")
        self.assertEqual(response.status_code, 401)

    def test_invalid_credentials_are_401(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": "api_kawaida", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_me_returns_kawaida_capabilities(self):
        self._auth("api_kawaida")
        response = self.client.get("/api/v1/me/")
        self.assertEqual(response.status_code, 200)
        caps = response.data["capabilities"]
        self.assertEqual(response.data["cheo"], "Mwalimu wa Kawaida")
        self.assertIn(CAP_ATTENDANCE, caps)
        self.assertIn(CAP_VIEW_STUDENTS, caps)
        self.assertNotIn(CAP_FEES, caps)

    def test_me_jaji_has_exams_not_attendance(self):
        self._auth("api_jaji")
        response = self.client.get("/api/v1/me/")
        self.assertEqual(response.status_code, 200)
        caps = response.data["capabilities"]
        self.assertIn(CAP_EXAMS, caps)
        self.assertNotIn(CAP_ATTENDANCE, caps)

    def test_office_denied_directory_and_attendance(self):
        self._auth("api_ofisi")
        self.assertEqual(self.client.get("/api/v1/madarasa/").status_code, 403)
        payload = self._roll_payload()
        self.assertEqual(self.client.post("/api/v1/mahudhurio/", payload, format="json").status_code, 403)

    def test_bare_user_denied_roster(self):
        self._auth("api_bare")
        url = f"/api/v1/madarasa/{self.darasa.id}/wanafunzi/"
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_roster_excludes_archived_and_parent_phones(self):
        self._auth("api_kawaida")
        response = self.client.get(f"/api/v1/madarasa/{self.darasa.id}/wanafunzi/")
        self.assertEqual(response.status_code, 200)
        ids = {row["id"] for row in response.data}
        self.assertEqual(ids, {self.s1.id, self.s2.id})
        self.assertNotIn(self.archived.id, ids)
        for row in response.data:
            self.assertNotIn("namba_ya_simu_mzazi", row)
            self.assertIn("jina_kamili", row)
            self.assertIn("namba_ya_usajili", row)

    def test_jaji_can_read_roster_not_write_attendance(self):
        self._auth("api_jaji")
        self.assertEqual(
            self.client.get(f"/api/v1/madarasa/{self.darasa.id}/wanafunzi/").status_code,
            200,
        )
        self.assertEqual(self.client.get("/api/v1/madarasa/").status_code, 200)
        payload = self._roll_payload()
        self.assertEqual(
            self.client.post("/api/v1/mahudhurio/", payload, format="json").status_code,
            403,
        )

    def test_kawaida_records_attendance_batch(self):
        self._auth("api_kawaida")
        payload = self._roll_payload(yupo_map={self.s1.id: False})
        response = self.client.post("/api/v1/mahudhurio/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.data["idadi"], 2)
        self.assertEqual(
            Hudhurio.objects.filter(tarehe=date.today(), aina_ya_rekodi="Kawaida").count(),
            2,
        )
        absent = Hudhurio.objects.get(mwanafunzi=self.s1, tarehe=date.today())
        self.assertFalse(absent.yupo)
        self.assertEqual(absent.sababu_kama_hayupo, "mgonjwa")

    def test_duplicate_attendance_returns_409(self):
        self._auth("api_kawaida")
        payload = self._roll_payload()
        first = self.client.post("/api/v1/mahudhurio/", payload, format="json")
        self.assertEqual(first.status_code, 201)
        second = self.client.post("/api/v1/mahudhurio/", payload, format="json")
        self.assertEqual(second.status_code, 409)
        self.assertEqual(
            Hudhurio.objects.filter(tarehe=date.today(), aina_ya_rekodi="Kawaida").count(),
            2,
        )

    def test_incomplete_roster_returns_400(self):
        self._auth("api_kawaida")
        payload = self._roll_payload()
        payload["rekodi"] = payload["rekodi"][:1]
        response = self.client.post("/api/v1/mahudhurio/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Hudhurio.objects.count(), 0)

    def test_get_mahudhurio_requires_darasa(self):
        self._auth("api_kawaida")
        self.assertEqual(self.client.get("/api/v1/mahudhurio/").status_code, 400)
        listed = self.client.get(f"/api/v1/mahudhurio/?darasa={self.darasa.id}")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data, [])

    def test_mkuu_has_directory_capability(self):
        self._auth("api_mkuu")
        response = self.client.get("/api/v1/me/")
        self.assertIn(CAP_VIEW_DIRECTORY, response.data["capabilities"])
        self.assertIn(CAP_FEES, response.data["capabilities"])
        self.assertEqual(self.client.get("/api/v1/madarasa/").status_code, 200)

    def test_catalog_sidebar_lists_respect_capabilities(self):
        self._auth("api_kawaida")
        self.assertEqual(self.client.get("/api/v1/mwanzo/").status_code, 200)
        walimu = self.client.get("/api/v1/walimu/")
        self.assertEqual(walimu.status_code, 200)
        names = {row["username"] for row in walimu.data}
        self.assertIn("api_kawaida", names)
        students = self.client.get("/api/v1/wanafunzi/")
        self.assertEqual(students.status_code, 200)
        ids = {row["id"] for row in students.data}
        self.assertEqual(ids, {self.s1.id, self.s2.id})
        for row in students.data:
            self.assertNotIn("namba_ya_simu_mzazi", row)
        self.assertEqual(self.client.get("/api/v1/watoro/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/malipo/").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/mawasiliano/").status_code, 403)

        self._auth("api_ofisi")
        self.assertEqual(self.client.get("/api/v1/walimu/").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/malipo/").status_code, 200)
        contacts = self.client.get("/api/v1/mawasiliano/")
        self.assertEqual(contacts.status_code, 200)
        phones = {row["id"]: row["namba_ya_simu_mzazi"] for row in contacts.data}
        self.assertEqual(phones[self.s1.id], "0771111111")

        self._auth("api_mkuu")
        self.assertEqual(self.client.get("/api/v1/mwaka/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/hamisha/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/ukaguzi/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/aina-malipo/").status_code, 200)


@HOSTS
@NO_THROTTLE
class ApiV1SabaqExamsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.darasa = Darasa.objects.create(jina="Darasa API P3")
        self.student = Mwanafunzi.objects.create(
            jina_kamili="API P3 Student",
            darasa=self.darasa,
        )
        self.hifdhu = Somo.objects.create(
            jina="Hifdhu API",
            ni_la_hifdhu=True,
            darasa=self.darasa,
        )
        self.student.programu_ya_usiku = self.hifdhu
        self.student.save(update_fields=["programu_ya_usiku"])
        self.fiqhi = Somo.objects.create(
            jina="Fiqhi API",
            ni_la_hifdhu=False,
            darasa=self.darasa,
        )
        self.exam = Mtihani.objects.create(
            somo=self.fiqhi,
            jina_la_mtihani="Mtihani wa kwanza",
            tarehe=date.today(),
        )
        self.kawaida = create_user_with_cheo("p3_kawaida", "Mwalimu wa Kawaida")
        self.jaji = create_user_with_cheo("p3_jaji", "Jaji")
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.office = User.objects.create_user("p3_ofisi", password="pass12345")
        ct = ContentType.objects.get_for_model(Malipo)
        perm = Permission.objects.get(content_type=ct, codename="add_malipo")
        self.office.user_permissions.add(perm)

    def _auth(self, username):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": username, "password": "pass12345"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_kawaida_records_sabaq_and_maendeleo(self):
        self._auth("p3_kawaida")
        sabaq = self.client.post(
            "/api/v1/sabaq/",
            {
                "mwanafunzi": self.student.id,
                "aina_ya_rekodi": "Usiku",
                "sabaq_sura": "Al-Fatiha",
                "sabaq_aya_kuanzia": 1,
                "sabaq_aya_kuishia": 7,
                "sabaq_hali": "Kajua",
            },
            format="json",
        )
        self.assertEqual(sabaq.status_code, 201, sabaq.content)
        self.assertEqual(RekodiHifdhu.objects.count(), 1)
        progress = self.client.post(
            "/api/v1/maendeleo/",
            {
                "mwanafunzi": self.student.id,
                "somo": self.fiqhi.id,
                "mada_iliyosomwa": "Udhu",
                "hali": "Ameelewa",
            },
            format="json",
        )
        self.assertEqual(progress.status_code, 201, progress.content)
        self.assertEqual(RekodiMaendeleoMchana.objects.count(), 1)

    def test_jaji_denied_sabaq_allowed_maksi(self):
        self._auth("p3_jaji")
        self.assertEqual(
            self.client.post(
                "/api/v1/sabaq/",
                {"mwanafunzi": self.student.id, "aina_ya_rekodi": "Darasa"},
                format="json",
            ).status_code,
            403,
        )
        listed = self.client.get(f"/api/v1/mitihani/?somo={self.fiqhi.id}")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data), 1)
        saved = self.client.put(
            f"/api/v1/mitihani/{self.exam.id}/matokeo/",
            {"rekodi": [{"mwanafunzi": self.student.id, "maksi": 81}]},
            format="json",
        )
        self.assertEqual(saved.status_code, 200, saved.content)
        row = Matokeo.objects.get(mtihani=self.exam, mwanafunzi=self.student)
        self.assertEqual(row.maksi, 81)

    def test_office_denied_sabaq(self):
        self._auth("p3_ofisi")
        self.assertEqual(
            self.client.post(
                "/api/v1/sabaq/",
                {"mwanafunzi": self.student.id, "aina_ya_rekodi": "Darasa"},
                format="json",
            ).status_code,
            403,
        )

    def test_maksi_out_of_range_rejected(self):
        self._auth("p3_jaji")
        response = self.client.put(
            f"/api/v1/mitihani/{self.exam.id}/matokeo/",
            {"rekodi": [{"mwanafunzi": self.student.id, "maksi": 101}]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Matokeo.objects.count(), 0)

    def test_hifdhu_somo_rejected_for_maendeleo(self):
        self._auth("p3_kawaida")
        response = self.client.post(
            "/api/v1/maendeleo/",
            {
                "mwanafunzi": self.student.id,
                "somo": self.hifdhu.id,
                "mada_iliyosomwa": "Juzuu",
                "hali": "Ameelewa",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RekodiMaendeleoMchana.objects.count(), 0)
