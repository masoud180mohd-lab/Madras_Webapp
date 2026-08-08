from datetime import date
from decimal import Decimal

from django.test import TestCase

from usimamizi.forms import MalipoForm, build_hudhurio_rows, parse_maksi_post
from usimamizi.models import Mwanafunzi


class FormsHardeningTests(TestCase):
    def test_parse_maksi_rejects_out_of_range(self):
        student = Mwanafunzi.objects.create(jina_kamili="Maksi Bound")
        scores, errors = parse_maksi_post([student], {f"maksi_{student.id}": "150"})
        self.assertEqual(scores, {})
        self.assertTrue(errors)

    def test_malipo_form_blocks_overpay(self):
        form = MalipoForm(
            {"kiasi": "5000", "njia": "Cash", "maelezo": ""},
            max_kiasi=Decimal("1000"),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("kiasi", form.errors)

    def test_build_hudhurio_rows_bulk_shape(self):
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
