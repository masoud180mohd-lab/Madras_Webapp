from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from usimamizi.dashboard import build_dashboard_context
from usimamizi.models import (
    AinaMalipo,
    Darasa,
    Hudhurio,
    Malipo,
    Mtihani,
    Mwanafunzi,
    Somo,
    Tangazo,
)
from usimamizi.tests.helpers import HOSTS, create_user_with_cheo


@HOSTS
class DashboardHomeTests(TestCase):
    def setUp(self):
        self.mkuu = create_user_with_cheo("mkuu_dash", "Mwalimu Mkuu")
        self.kawaida = create_user_with_cheo("kawaida_dash", "Mwalimu wa Kawaida")
        self.jaji = create_user_with_cheo("jaji_dash", "Jaji")
        self.darasa = Darasa.objects.create(jina="Darasa Dash")
        self.student = Mwanafunzi.objects.create(
            jina_kamili="Dash Student",
            darasa=self.darasa,
        )
        Tangazo.objects.create(
            kichwa_cha_habari="Tangazo la jaribio",
            maelezo="Maelezo ya tangazo.",
        )

    def test_home_renders_for_mkuu(self):
        self.client.login(username="mkuu_dash", password="pass12345")
        response = self.client.get(reverse("mwanzo"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Karibu")
        self.assertContains(response, "Vitendo haraka")
        self.assertContains(response, "Tangazo la jaribio")
        self.assertContains(response, "Malipo")

    def test_kawaida_sees_attendance_not_fees(self):
        self.client.login(username="kawaida_dash", password="pass12345")
        response = self.client.get(reverse("mwanzo"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mahudhurio leo")
        self.assertNotContains(response, "Ada na risiti")
        ctx = build_dashboard_context(self.kawaida)
        labels = [m["label"] for m in ctx["vipimo"]] + [
            a["label"] for a in ctx["vitendo_haraka"]
        ]
        self.assertNotIn("Malipo leo", labels)
        self.assertNotIn("Malipo", labels)

    def test_jaji_sees_exams_not_attendance_metric(self):
        ctx = build_dashboard_context(self.jaji, leo=date(2026, 8, 8))
        labels = [m["label"] for m in ctx["vipimo"]]
        self.assertIn("Mitihani (siku 30)", labels)
        self.assertNotIn("Mahudhurio leo", labels)
        self.assertNotIn("Malipo leo", labels)

    def test_attendance_metric_counts_recorded_class(self):
        Hudhurio.objects.create(
            mwanafunzi=self.student,
            tarehe=date(2026, 8, 8),
            aina_ya_rekodi="Kawaida",
            yupo=True,
        )
        ctx = build_dashboard_context(self.kawaida, leo=date(2026, 8, 8))
        mahudhurio = next(m for m in ctx["vipimo"] if m["label"] == "Mahudhurio leo")
        self.assertEqual(mahudhurio["value"], "1/1")

    def test_fees_metric_for_mkuu(self):
        aina = AinaMalipo.objects.create(
            jina="Ada Dash",
            kiasi_kinachotakiwa=Decimal("5000"),
        )
        Malipo.objects.create(
            mwanafunzi=self.student,
            aina_ya_malipo=aina,
            kiasi_kilicholipwa=Decimal("1000"),
            njia_ya_malipo="Cash",
        )
        # tarehe_ya_malipo is auto_now_add — use today
        ctx = build_dashboard_context(self.mkuu)
        labels = [m["label"] for m in ctx["vipimo"]]
        self.assertIn("Malipo leo", labels)
        self.assertIn("Wanaodaiwa", labels)
        self.assertIsNotNone(ctx["ufuatiliaji_deni"])
        self.assertEqual(ctx["ufuatiliaji_deni"]["idadi"], 1)
        self.assertEqual(ctx["ufuatiliaji_deni"]["jumla"], Decimal("4000"))

    def test_attendance_followup_lists_absent_today(self):
        Hudhurio.objects.create(
            mwanafunzi=self.student,
            tarehe=date(2026, 8, 8),
            aina_ya_rekodi="Kawaida",
            yupo=False,
        )
        ctx = build_dashboard_context(self.kawaida, leo=date(2026, 8, 8))
        follow = ctx["ufuatiliaji_mahudhurio"]
        self.assertIsNotNone(follow)
        self.assertEqual(follow["hayupo_leo"], 1)
        self.assertEqual(len(follow["orodha"]), 1)
        self.assertEqual(follow["orodha"][0]["mwanafunzi"].id, self.student.id)
        labels = [m["label"] for m in ctx["vipimo"]]
        self.assertIn("Watoro wiki", labels)

    def test_manage_students_action_only_for_mkuu(self):
        mkuu_ctx = build_dashboard_context(self.mkuu)
        kawaida_ctx = build_dashboard_context(self.kawaida)
        mkuu_labels = [a["label"] for a in mkuu_ctx["vitendo_haraka"]]
        kawaida_labels = [a["label"] for a in kawaida_ctx["vitendo_haraka"]]
        self.assertIn("Sajili mwanafunzi", mkuu_labels)
        self.assertNotIn("Sajili mwanafunzi", kawaida_labels)

    def test_pending_exams_metric(self):
        somo = Somo.objects.create(jina="Fiqhi Dash", darasa=self.darasa)
        Mtihani.objects.create(
            somo=somo,
            jina_la_mtihani="Jaribio Dash",
            tarehe=date(2026, 8, 1),
        )
        ctx = build_dashboard_context(self.jaji, leo=date(2026, 8, 8))
        bila = next(m for m in ctx["vipimo"] if m["label"] == "Bila maksi")
        self.assertEqual(bila["value"], 1)
