import json
from datetime import date, time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from worship.models import Hymnal, HymnalAlias, Song, WorshipService, WorshipServiceSong

CustomUser = get_user_model()


def _make_worship_user(**kwargs):
    username = kwargs.pop("username", "worshipper")
    defaults = {
        "password": "testpass123",
        "type": CustomUser.Types.REGULAR,
    }
    defaults.update(kwargs)
    return CustomUser.objects.create_user(username=username, email=f"{username}@test.com", **defaults)


class WorshipAccessMixinTestCase(TestCase):
    def setUp(self):
        self.regular = _make_worship_user(username="regular")
        self.staff = _make_worship_user(username="staff", is_staff=True)
        self.superuser = _make_worship_user(username="super", is_superuser=True)
        self.outsider = CustomUser.objects.create_user(
            username="outsider", password="testpass123", email="outsider@test.com",
            type=CustomUser.Types.SIMPLE_USER
        )

    def test_regular_can_access_list(self):
        self.client.force_login(self.regular)
        response = self.client.get(reverse("worship:service-list"))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_access_list(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("worship:service-list"))
        self.assertEqual(response.status_code, 200)

    def test_superuser_can_access_list(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("worship:service-list"))
        self.assertEqual(response.status_code, 200)

    def test_not_authenticated_redirects(self):
        response = self.client.get(reverse("worship:service-list"))
        self.assertIn(response.status_code, [302, 403])

    def test_outsider_forbidden(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("worship:service-list"))
        self.assertIn(response.status_code, [302, 403])


class ServiceListViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)

    def test_list_returns_200(self):
        response = self.client.get(reverse("worship:service-list"))
        self.assertEqual(response.status_code, 200)

    def test_list_shows_services(self):
        WorshipService.objects.create(title="Culto A", service_date=date(2026, 5, 1))
        WorshipService.objects.create(title="Culto B", service_date=date(2026, 5, 8))
        response = self.client.get(reverse("worship:service-list"))
        self.assertEqual(len(response.context["services"]), 2)

    def test_list_filter_by_title(self):
        WorshipService.objects.create(title="Culto de Ceia", service_date=date(2026, 5, 1))
        WorshipService.objects.create(title="Culto Regular", service_date=date(2026, 5, 8))
        response = self.client.get(reverse("worship:service-list") + "?q=Ceia")
        self.assertEqual(len(response.context["services"]), 1)
        self.assertEqual(response.context["services"][0].title, "Culto de Ceia")

    def test_list_empty(self):
        response = self.client.get(reverse("worship:service-list"))
        self.assertEqual(len(response.context["services"]), 0)


class ServiceCreateViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)

    def test_create_get(self):
        response = self.client.get(reverse("worship:service-create"))
        self.assertEqual(response.status_code, 200)

    def test_create_post_valid(self):
        response = self.client.post(reverse("worship:service-create"), {
            "title": "Culto Teste",
            "service_kind": "REGULAR",
            "service_date": "2026-05-01",
            "service_time": "19:00",
            "leader_dirigente": "Breno",
            "leader_regente": "Jhonathan",
            "leader_musician": "Mellyne",
            "program_html": "<ol><li>Hino</li></ol>",
            "notes": "",
        })
        svc = WorshipService.objects.first()
        self.assertIsNotNone(svc)
        self.assertRedirects(response, reverse("worship:service-detail", kwargs={"pk": svc.pk}))
        self.assertEqual(svc.created_by, self.user)

    def test_create_leaders_auto_composed(self):
        self.client.post(reverse("worship:service-create"), {
            "title": "Culto",
            "service_kind": "REGULAR",
            "service_date": "2026-05-01",
            "leader_dirigente": "Breno",
            "leader_regente": "Jhonathan",
            "leader_musician": "Mellyne",
            "program_html": "",
            "notes": "",
        })
        svc = WorshipService.objects.first()
        self.assertEqual(svc.leaders_text, "Dirigente: Breno / Regente: Jhonathan / Pianista: Mellyne")

    def test_create_leaders_empty_when_all_blank(self):
        self.client.post(reverse("worship:service-create"), {
            "title": "Culto",
            "service_kind": "REGULAR",
            "service_date": "2026-05-01",
            "leader_dirigente": "",
            "leader_regente": "",
            "leader_musician": "",
            "program_html": "",
            "notes": "",
        })
        svc = WorshipService.objects.first()
        self.assertEqual(svc.leaders_text, "")

    def test_create_only_dirigente(self):
        self.client.post(reverse("worship:service-create"), {
            "title": "Culto",
            "service_kind": "REGULAR",
            "service_date": "2026-05-01",
            "leader_dirigente": "Breno",
            "leader_regente": "",
            "leader_musician": "",
            "program_html": "",
            "notes": "",
        })
        svc = WorshipService.objects.first()
        self.assertEqual(svc.leaders_text, "Dirigente: Breno")


class ServiceUpdateViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(
            title="Culto Original",
            service_date=date(2026, 5, 1),
        )

    def test_update_get(self):
        response = self.client.get(reverse("worship:service-edit", kwargs={"pk": self.svc.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_post(self):
        response = self.client.post(
            reverse("worship:service-edit", kwargs={"pk": self.svc.pk}),
            {
                "title": "Culto Editado",
                "service_kind": "COMMUNION",
                "service_date": "2026-05-15",
                "leader_dirigente": "Pr. João",
                "leader_regente": "",
                "leader_musician": "",
                "program_html": "",
                "notes": "",
            },
        )
        self.svc.refresh_from_db()
        self.assertEqual(self.svc.title, "Culto Editado")
        self.assertEqual(self.svc.service_kind, "COMMUNION")
        self.assertEqual(self.svc.leaders_text, "Dirigente: Pr. João")

    def test_update_recompose_leaders(self):
        self.svc.leaders_text = "Dirigente: Antigo"
        self.svc.save()
        self.client.post(
            reverse("worship:service-edit", kwargs={"pk": self.svc.pk}),
            {
                "title": "Culto",
                "service_kind": "REGULAR",
                "service_date": "2026-05-01",
                "leader_dirigente": "Novo",
                "leader_regente": "Regente Novo",
                "leader_musician": "",
                "program_html": "",
                "notes": "",
            },
        )
        self.svc.refresh_from_db()
        self.assertEqual(self.svc.leaders_text, "Dirigente: Novo / Regente: Regente Novo")


class ServiceDeleteViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(title="Culto", service_date=date(2026, 5, 1))

    def test_delete_post(self):
        response = self.client.post(reverse("worship:service-delete", kwargs={"pk": self.svc.pk}))
        self.assertRedirects(response, reverse("worship:service-list"))
        self.assertFalse(WorshipService.objects.filter(pk=self.svc.pk).exists())

    def test_delete_cascades_songs(self):
        WorshipServiceSong.objects.create(service=self.svc, song_snapshot="Hino 1")
        self.client.post(reverse("worship:service-delete", kwargs={"pk": self.svc.pk}))
        self.assertEqual(WorshipServiceSong.objects.count(), 0)

    def test_delete_not_found(self):
        response = self.client.post(reverse("worship:service-delete", kwargs={"pk": 9999}))
        self.assertEqual(response.status_code, 404)


class ServiceDetailViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)
        self.hymnal = baker.make(Hymnal, title="CC")
        self.song = baker.make(Song, title="A Deus demos glória")
        self.svc = WorshipService.objects.create(
            title="Culto",
            service_date=date(2026, 5, 1),
            program_html="<ol><li>CC 291 - A Deus demos glória</li></ol>",
        )

    def test_detail_get(self):
        response = self.client.get(reverse("worship:service-detail", kwargs={"pk": self.svc.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["service"], self.svc)

    def test_detail_context_song_choices(self):
        baker.make(Song, _quantity=3)
        response = self.client.get(reverse("worship:service-detail", kwargs={"pk": self.svc.pk}))
        self.assertEqual(response.context["song_choices"].count(), 4)

    def test_detail_context_pending_songs(self):
        WorshipServiceSong.objects.create(
            service=self.svc,
            song_snapshot="Pendente",
            resolution_status=WorshipServiceSong.RESOLUTION_PENDING_REVIEW,
        )
        WorshipServiceSong.objects.create(
            service=self.svc,
            song_snapshot="Vinculada",
            resolution_status=WorshipServiceSong.RESOLUTION_LINKED,
        )
        response = self.client.get(reverse("worship:service-detail", kwargs={"pk": self.svc.pk}))
        self.assertEqual(len(response.context["pending_songs"]), 1)

    def test_detail_font_scale_clamped(self):
        self.svc.program_font_scale = 200
        self.svc.save()
        response = self.client.get(reverse("worship:service-detail", kwargs={"pk": self.svc.pk}))
        self.assertEqual(response.context["program_font_scale"], 130)

    def test_detail_not_found(self):
        response = self.client.get(reverse("worship:service-detail", kwargs={"pk": 9999}))
        self.assertEqual(response.status_code, 404)


class ServiceDuplicateViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(
            title="Culto Original",
            service_kind=WorshipService.KIND_COMMUNION,
            service_date=date(2026, 5, 1),
            program_html="<ol><li>Hino</li></ol>",
            leaders_text="Dirigente: Breno",
        )
        self.song_obj = baker.make(Song, title="Hino 1")
        WorshipServiceSong.objects.create(
            service=self.svc,
            song_snapshot="Hino 1",
            song=self.song_obj,
            resolution_status=WorshipServiceSong.RESOLUTION_LINKED,
            match_confidence=1.0,
        )

    def test_duplicate_creates_copy(self):
        response = self.client.post(reverse("worship:service-duplicate", kwargs={"pk": self.svc.pk}))
        self.assertEqual(WorshipService.objects.count(), 2)
        new_svc = WorshipService.objects.latest("id")
        self.assertRedirects(response, reverse("worship:service-edit", kwargs={"pk": new_svc.pk}))
        self.assertEqual(new_svc.title, "Culto Original")
        self.assertNotEqual(new_svc.pk, self.svc.pk)

    def test_duplicate_copies_songs(self):
        self.client.post(reverse("worship:service-duplicate", kwargs={"pk": self.svc.pk}))
        new_svc = WorshipService.objects.latest("id")
        self.assertEqual(new_svc.sung_songs.count(), 1)
        copied = new_svc.sung_songs.first()
        self.assertEqual(copied.song_snapshot, "Hino 1")
        self.assertEqual(copied.resolution_status, WorshipServiceSong.RESOLUTION_LINKED)

    def test_duplicate_not_found(self):
        response = self.client.post(reverse("worship:service-duplicate", kwargs={"pk": 9999}))
        self.assertEqual(response.status_code, 404)


class FontScaleViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(title="Culto", service_date=date(2026, 5, 1))

    def test_increase(self):
        self.client.post(
            reverse("worship:service-font-scale", kwargs={"pk": self.svc.pk}),
            {"action": "increase"},
        )
        self.svc.refresh_from_db()
        self.assertEqual(self.svc.program_font_scale, 105)

    def test_decrease(self):
        self.client.post(
            reverse("worship:service-font-scale", kwargs={"pk": self.svc.pk}),
            {"action": "decrease"},
        )
        self.svc.refresh_from_db()
        self.assertEqual(self.svc.program_font_scale, 95)

    def test_reset(self):
        self.svc.program_font_scale = 120
        self.svc.save()
        self.client.post(
            reverse("worship:service-font-scale", kwargs={"pk": self.svc.pk}),
            {"action": "reset"},
        )
        self.svc.refresh_from_db()
        self.assertEqual(self.svc.program_font_scale, 100)

    def test_clamp_at_maximum(self):
        self.svc.program_font_scale = 130
        self.svc.save()
        self.client.post(
            reverse("worship:service-font-scale", kwargs={"pk": self.svc.pk}),
            {"action": "increase"},
        )
        self.svc.refresh_from_db()
        self.assertEqual(self.svc.program_font_scale, 130)

    def test_clamp_at_minimum(self):
        self.svc.program_font_scale = 75
        self.svc.save()
        self.client.post(
            reverse("worship:service-font-scale", kwargs={"pk": self.svc.pk}),
            {"action": "decrease"},
        )
        self.svc.refresh_from_db()
        self.assertEqual(self.svc.program_font_scale, 75)


class ServicePrintViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(
            title="Culto",
            service_date=date(2026, 5, 1),
            program_html="<ol><li>Hino</li></ol>",
        )

    def test_print_returns_200(self):
        response = self.client.get(reverse("worship:service-print", kwargs={"pk": self.svc.pk}))
        self.assertEqual(response.status_code, 200)

    def test_print_context_has_church_info(self):
        response = self.client.get(reverse("worship:service-print", kwargs={"pk": self.svc.pk}))
        self.assertIn("church_info", response.context)


class ServicePdfViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(
            title="Culto PDF",
            service_date=date(2026, 5, 1),
            program_html="<ol><li>Hino</li></ol>",
        )

    def test_pdf_1up(self):
        response = self.client.get(
            reverse("worship:service-pdf", kwargs={"pk": self.svc.pk}) + "?layout=1up"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("1up", response["Content-Disposition"])

    def test_pdf_2up(self):
        response = self.client.get(
            reverse("worship:service-pdf", kwargs={"pk": self.svc.pk}) + "?layout=2up"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("2up", response["Content-Disposition"])

    def test_pdf_default_layout(self):
        response = self.client.get(
            reverse("worship:service-pdf", kwargs={"pk": self.svc.pk})
        )
        self.assertIn("1up", response["Content-Disposition"])


class ServiceImportViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)

    def test_import_get(self):
        response = self.client.get(reverse("worship:service-import"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    @patch("worship.views.service_views.generate_service_with_llm")
    def test_import_preview(self, mock_llm):
        mock_llm.return_value = {
            "title": "Culto de Ceia",
            "service_date": "2026-05-01",
            "service_kind": "COMMUNION",
            "leaders_text": "Dirigente: Pr.",
            "program_html": "<ol><li>Hino</li></ol>",
            "songs": [{"order_ref": 1, "song_snapshot": "CC 291"}],
            "confidence": 0.9,
            "source": "llm",
        }
        response = self.client.post(reverse("worship:service-import"), {
            "raw_text": "Texto do culto...",
            "model_hint": "",
            "action": "preview",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("preview", response.context)
        self.assertEqual(response.context["preview"]["title"], "Culto de Ceia")

    @patch("worship.views.service_views.generate_service_with_llm")
    def test_import_create(self, mock_llm):
        mock_llm.return_value = {
            "title": "Culto Criado",
            "service_date": "2026-06-01",
            "service_kind": "REGULAR",
            "leaders_text": "",
            "program_html": "<ol><li>Hino</li></ol>",
            "songs": [],
            "confidence": 0.9,
            "source": "llm",
        }
        payload = json.dumps(mock_llm.return_value)
        response = self.client.post(reverse("worship:service-import"), {
            "raw_text": "Texto",
            "model_hint": "",
            "action": "create",
            "parsed_payload": payload,
        })
        svc = WorshipService.objects.first()
        self.assertIsNotNone(svc)
        self.assertEqual(svc.title, "Culto Criado")
        self.assertRedirects(response, reverse("worship:service-detail", kwargs={"pk": svc.pk}))

    @patch("worship.views.service_views.generate_service_with_llm")
    def test_import_create_no_date_returns_error(self, mock_llm):
        mock_llm.return_value = {
            "title": "Sem Data",
            "service_date": None,
            "service_kind": "REGULAR",
            "leaders_text": "",
            "program_html": "",
            "songs": [],
            "confidence": 0.5,
            "source": "llm",
        }
        payload = json.dumps(mock_llm.return_value)
        response = self.client.post(reverse("worship:service-import"), {
            "raw_text": "Texto",
            "model_hint": "",
            "action": "create",
            "parsed_payload": payload,
        })
        self.assertEqual(WorshipService.objects.count(), 0)


class ServiceGenerateProgramViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_worship_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(
            title="Culto",
            service_date=date(2026, 5, 1),
        )

    @patch("worship.views.service_views.generate_service_with_llm")
    def test_generate_overwrites_program(self, mock_llm):
        mock_llm.return_value = {
            "title": "Novo Título",
            "service_date": "2026-05-01",
            "service_kind": "REGULAR",
            "leaders_text": "Dirigente: Novo",
            "program_html": "<ol><li>Novo hino</li></ol>",
            "songs": [{"order_ref": 1, "song_snapshot": "CC 100"}],
            "confidence": 0.9,
            "source": "llm",
        }
        response = self.client.post(
            reverse("worship:service-generate", kwargs={"pk": self.svc.pk}),
            {"raw_text": "Texto", "model_hint": ""},
        )
        self.svc.refresh_from_db()
        self.assertEqual(self.svc.title, "Novo Título")
        self.assertEqual(self.svc.leaders_text, "Dirigente: Novo")

    def test_generate_empty_text_shows_error(self):
        response = self.client.post(
            reverse("worship:service-generate", kwargs={"pk": self.svc.pk}),
            {"raw_text": "", "model_hint": ""},
        )
        self.svc.refresh_from_db()
        self.assertEqual(self.svc.title, "Culto")
