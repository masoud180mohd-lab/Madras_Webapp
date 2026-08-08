from datetime import date, timedelta

from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase

from usimamizi.models import Darasa, Hudhurio, Matokeo, Mtihani, Mwanafunzi, Somo


class MwanafunziRegistrationTests(TestCase):
    def test_auto_assigns_mr_numbers_sequentially(self):
        first = Mwanafunzi.objects.create(jina_kamili="Ali Test A")
        second = Mwanafunzi.objects.create(jina_kamili="Ali Test B")

        self.assertRegex(first.namba_ya_usajili, r"^MR-\d{3,}$")
        self.assertRegex(second.namba_ya_usajili, r"^MR-\d{3,}$")

        first_n = int(first.namba_ya_usajili.split("-")[1])
        second_n = int(second.namba_ya_usajili.split("-")[1])
        self.assertEqual(second_n, first_n + 1)

    def test_preserves_explicit_registration_number(self):
        student = Mwanafunzi.objects.create(
            jina_kamili="Ali Explicit",
            namba_ya_usajili="MR-900",
        )
        self.assertEqual(student.namba_ya_usajili, "MR-900")


class HudhurioIntegrityTests(TestCase):
    def setUp(self):
        self.student = Mwanafunzi.objects.create(jina_kamili="Hudhurio Student")
        self.day = date(2026, 5, 1)

    def test_allows_one_record_per_day_and_type(self):
        Hudhurio.objects.create(
            mwanafunzi=self.student,
            tarehe=self.day,
            aina_ya_rekodi="Kawaida",
            yupo=True,
        )
        Hudhurio.objects.create(
            mwanafunzi=self.student,
            tarehe=self.day,
            aina_ya_rekodi="Hifdhu",
            yupo=True,
        )
        self.assertEqual(Hudhurio.objects.filter(mwanafunzi=self.student).count(), 2)

    def test_rejects_duplicate_same_day_and_type(self):
        Hudhurio.objects.create(
            mwanafunzi=self.student,
            tarehe=self.day,
            aina_ya_rekodi="Kawaida",
            yupo=True,
        )
        with self.assertRaises(IntegrityError):
            Hudhurio.objects.create(
                mwanafunzi=self.student,
                tarehe=self.day,
                aina_ya_rekodi="Kawaida",
                yupo=False,
            )

    def test_allows_same_type_on_different_days(self):
        Hudhurio.objects.create(
            mwanafunzi=self.student,
            tarehe=self.day,
            aina_ya_rekodi="Kawaida",
        )
        Hudhurio.objects.create(
            mwanafunzi=self.student,
            tarehe=self.day + timedelta(days=1),
            aina_ya_rekodi="Kawaida",
        )
        self.assertEqual(
            Hudhurio.objects.filter(mwanafunzi=self.student, aina_ya_rekodi="Kawaida").count(),
            2,
        )


class MatokeoIntegrityTests(TestCase):
    def setUp(self):
        self.darasa = Darasa.objects.create(jina="Darasa Test")
        self.somo = Somo.objects.create(jina="Fiqhi Test", darasa=self.darasa)
        self.mtihani = Mtihani.objects.create(
            somo=self.somo,
            jina_la_mtihani="Jaribio",
            tarehe=date(2026, 6, 1),
        )
        self.student = Mwanafunzi.objects.create(
            jina_kamili="Matokeo Student",
            darasa=self.darasa,
        )

    def test_rejects_duplicate_marks_for_same_exam_student(self):
        Matokeo.objects.create(mtihani=self.mtihani, mwanafunzi=self.student, maksi=70)
        with self.assertRaises(IntegrityError):
            Matokeo.objects.create(mtihani=self.mtihani, mwanafunzi=self.student, maksi=80)

    def test_update_or_create_keeps_single_row(self):
        Matokeo.objects.update_or_create(
            mtihani=self.mtihani,
            mwanafunzi=self.student,
            defaults={"maksi": 65},
        )
        Matokeo.objects.update_or_create(
            mtihani=self.mtihani,
            mwanafunzi=self.student,
            defaults={"maksi": 88},
        )
        self.assertEqual(
            Matokeo.objects.filter(mtihani=self.mtihani, mwanafunzi=self.student).count(),
            1,
        )
        self.assertEqual(
            Matokeo.objects.get(mtihani=self.mtihani, mwanafunzi=self.student).maksi,
            88,
        )


class RegistrationConcurrencyTests(TransactionTestCase):
    """IntegrityError retry path: colliding numbers must not leave blank/invalid rows."""

    def test_second_save_gets_next_number_after_collision_setup(self):
        first = Mwanafunzi.objects.create(jina_kamili="Race Student 1")
        n = int(first.namba_ya_usajili.split("-")[1])
        # Pretend another process reserved the next number.
        Mwanafunzi.objects.create(
            jina_kamili="Race Student Reserved",
            namba_ya_usajili=f"MR-{n + 1:03d}",
        )
        third = Mwanafunzi.objects.create(jina_kamili="Race Student 2")
        self.assertEqual(int(third.namba_ya_usajili.split("-")[1]), n + 2)


class FormsHardeningTests(TestCase):
    def test_parse_maksi_rejects_out_of_range(self):
        from usimamizi.forms import parse_maksi_post

        student = Mwanafunzi.objects.create(jina_kamili="Maksi Bound")
        scores, errors = parse_maksi_post([student], {f"maksi_{student.id}": "150"})
        self.assertEqual(scores, {})
        self.assertTrue(errors)

    def test_malipo_form_blocks_overpay(self):
        from decimal import Decimal
        from usimamizi.forms import MalipoForm

        form = MalipoForm(
            {"kiasi": "5000", "njia": "Cash", "maelezo": ""},
            max_kiasi=Decimal("1000"),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("kiasi", form.errors)

    def test_build_hudhurio_rows_bulk_shape(self):
        from datetime import date
        from usimamizi.forms import build_hudhurio_rows

        student = Mwanafunzi.objects.create(jina_kamili="Hudhurio Bulk")
        rows = build_hudhurio_rows(
            [student],
            {f"yupo_{student.id}": "on"},
            aina_ya_rekodi="Kawaida",
            tarehe=date(2026, 8, 1),
        )
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].yupo)
        self.assertEqual(rows[0].aina_ya_rekodi, "Kawaida")


class AuthZRoleMatrixTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from usimamizi.models import Mwalimu
        from usimamizi.permissions import (
            CAP_ATTENDANCE,
            CAP_EXAMS,
            CAP_FEES,
            CAP_MANAGE_STUDENTS,
            CAP_SABAQ,
            user_has_capability,
        )

        self.User = get_user_model()
        self.CAP_ATTENDANCE = CAP_ATTENDANCE
        self.CAP_EXAMS = CAP_EXAMS
        self.CAP_FEES = CAP_FEES
        self.CAP_MANAGE_STUDENTS = CAP_MANAGE_STUDENTS
        self.CAP_SABAQ = CAP_SABAQ
        self.user_has_capability = user_has_capability
        self.Mwalimu = Mwalimu

        self.student = Mwanafunzi.objects.create(jina_kamili="AuthZ Student")

        self.mkuu_user = self.User.objects.create_user("mkuu", password="pass12345")
        self.Mwalimu.objects.create(user=self.mkuu_user, cheo="Mwalimu Mkuu")

        self.kawaida_user = self.User.objects.create_user("kawaida", password="pass12345")
        self.Mwalimu.objects.create(user=self.kawaida_user, cheo="Mwalimu wa Kawaida")

        self.jaji_user = self.User.objects.create_user("jaji", password="pass12345")
        self.Mwalimu.objects.create(user=self.jaji_user, cheo="Jaji")

        self.office_user = self.User.objects.create_user("ofisi", password="pass12345")
        # Grant fee view/add only
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from usimamizi.models import Malipo

        ct = ContentType.objects.get_for_model(Malipo)
        for codename in ("view_malipo", "add_malipo"):
            perm = Permission.objects.get(content_type=ct, codename=codename)
            self.office_user.user_permissions.add(perm)

        self.bare_user = self.User.objects.create_user("bare", password="pass12345")

    def test_mkuu_has_fees_and_manage_students(self):
        self.assertTrue(self.user_has_capability(self.mkuu_user, self.CAP_FEES))
        self.assertTrue(self.user_has_capability(self.mkuu_user, self.CAP_MANAGE_STUDENTS))

    def test_kawaida_denied_fees_allowed_attendance(self):
        self.assertFalse(self.user_has_capability(self.kawaida_user, self.CAP_FEES))
        self.assertTrue(self.user_has_capability(self.kawaida_user, self.CAP_ATTENDANCE))
        self.assertTrue(self.user_has_capability(self.kawaida_user, self.CAP_SABAQ))
        self.assertTrue(self.user_has_capability(self.kawaida_user, self.CAP_EXAMS))

    def test_jaji_exams_not_fees_or_sabaq(self):
        self.assertTrue(self.user_has_capability(self.jaji_user, self.CAP_EXAMS))
        self.assertFalse(self.user_has_capability(self.jaji_user, self.CAP_FEES))
        self.assertFalse(self.user_has_capability(self.jaji_user, self.CAP_SABAQ))
        self.assertFalse(self.user_has_capability(self.jaji_user, self.CAP_ATTENDANCE))

    def test_office_fees_via_django_perms(self):
        self.assertTrue(self.user_has_capability(self.office_user, self.CAP_FEES))
        self.assertFalse(self.user_has_capability(self.office_user, self.CAP_ATTENDANCE))

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
        self.assertTrue(self.user_has_capability(self.jaji_user, self.CAP_EXAMS))

    def test_sabaq_without_mwalimu_redirects(self):
        # Office with sabaq perm but no Mwalimu profile
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from usimamizi.models import RekodiHifdhu

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
