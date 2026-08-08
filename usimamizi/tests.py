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
