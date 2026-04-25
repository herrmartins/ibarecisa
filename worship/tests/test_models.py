from datetime import date, time

from django.test import TestCase
from model_bakery import baker

from users.models import CustomUser
from worship.models import (
    Composer,
    Hymnal,
    HymnalAlias,
    Song,
    SongTheme,
    WorshipService,
    WorshipServiceSong,
)


class WorshipServiceModelTestCase(TestCase):
    def setUp(self):
        self.user = baker.make(CustomUser, username="worshipper")

    def test_creation_with_all_fields(self):
        svc = WorshipService.objects.create(
            title="Culto de Ceia",
            service_kind=WorshipService.KIND_COMMUNION,
            service_date=date(2026, 4, 20),
            service_time=time(19, 0),
            leader_dirigente="Breno",
            leader_regente="Jhonathan",
            leader_musician="Mellyne",
            leaders_text="Dirigente: Breno / Regente: Jhonathan / Pianista: Mellyne",
            program_html="<ol><li>Hino</li></ol>",
            notes="Observação",
            created_by=self.user,
        )
        self.assertEqual(svc.title, "Culto de Ceia")
        self.assertEqual(svc.service_kind, WorshipService.KIND_COMMUNION)
        self.assertEqual(svc.service_date, date(2026, 4, 20))
        self.assertEqual(svc.service_time, time(19, 0))
        self.assertEqual(svc.leaders_text, "Dirigente: Breno / Regente: Jhonathan / Pianista: Mellyne")
        self.assertEqual(svc.created_by, self.user)
        self.assertTrue(svc.ativo)

    def test_str_representation(self):
        svc = WorshipService.objects.create(
            title="Culto Regular",
            service_date=date(2026, 5, 1),
        )
        self.assertEqual(str(svc), "Culto Regular - 01/05/2026")

    def test_ordering(self):
        WorshipService.objects.create(title="A", service_date=date(2026, 1, 1))
        WorshipService.objects.create(title="B", service_date=date(2026, 3, 1))
        WorshipService.objects.create(title="C", service_date=date(2026, 2, 1))
        titles = list(WorshipService.objects.values_list("title", flat=True))
        self.assertEqual(titles, ["B", "C", "A"])

    def test_default_kind(self):
        svc = WorshipService.objects.create(title="T", service_date=date(2026, 1, 1))
        self.assertEqual(svc.service_kind, WorshipService.KIND_REGULAR)

    def test_default_font_scale(self):
        svc = WorshipService.objects.create(title="T", service_date=date(2026, 1, 1))
        self.assertEqual(svc.program_font_scale, 100)

    def test_optional_fields_blank(self):
        svc = WorshipService.objects.create(title="T", service_date=date(2026, 1, 1))
        self.assertEqual(svc.service_time, None)
        self.assertEqual(svc.leaders_text, "")
        self.assertEqual(svc.leader_dirigente, "")
        self.assertEqual(svc.program_html, "")
        self.assertEqual(svc.notes, "")
        self.assertIsNone(svc.created_by)

    def test_cascade_delete_removes_songs(self):
        svc = WorshipService.objects.create(title="T", service_date=date(2026, 1, 1))
        WorshipServiceSong.objects.create(service=svc, song_snapshot="Hino 1")
        WorshipServiceSong.objects.create(service=svc, song_snapshot="Hino 2")
        self.assertEqual(WorshipServiceSong.objects.count(), 2)
        svc.delete()
        self.assertEqual(WorshipServiceSong.objects.count(), 0)


class WorshipServiceSongModelTestCase(TestCase):
    def setUp(self):
        self.svc = WorshipService.objects.create(title="T", service_date=date(2026, 1, 1))
        self.hymnal = baker.make(Hymnal, title="HCC")
        self.song = baker.make(Song, title="A Deus demos glória", hymnal=self.hymnal, hymn_number=291)

    def test_defaults(self):
        wss = WorshipServiceSong.objects.create(
            service=self.svc,
            song_snapshot="CC 291",
        )
        self.assertEqual(wss.source, WorshipServiceSong.SOURCE_MANUAL)
        self.assertEqual(wss.resolution_status, WorshipServiceSong.RESOLUTION_PENDING_REVIEW)
        self.assertIsNone(wss.order_ref)
        self.assertIsNone(wss.song)
        self.assertEqual(wss.match_confidence, None)

    def test_str_returns_snapshot(self):
        wss = WorshipServiceSong.objects.create(service=self.svc, song_snapshot="CC 291")
        self.assertEqual(str(wss), "CC 291")

    def test_ordering(self):
        WorshipServiceSong.objects.create(service=self.svc, song_snapshot="C", order_ref=3)
        WorshipServiceSong.objects.create(service=self.svc, song_snapshot="A", order_ref=1)
        WorshipServiceSong.objects.create(service=self.svc, song_snapshot="B", order_ref=2)
        names = list(WorshipServiceSong.objects.values_list("song_snapshot", flat=True))
        self.assertEqual(names, ["A", "B", "C"])

    def test_ordering_with_ref_comes_first(self):
        WorshipServiceSong.objects.create(service=self.svc, song_snapshot="No order")
        WorshipServiceSong.objects.create(service=self.svc, song_snapshot="B", order_ref=2)
        WorshipServiceSong.objects.create(service=self.svc, song_snapshot="A", order_ref=1)
        with_ref = list(WorshipServiceSong.objects.filter(order_ref__isnull=False).values_list("song_snapshot", flat=True))
        self.assertEqual(with_ref, ["A", "B"])

    def test_linked_song_set_null_on_delete(self):
        wss = WorshipServiceSong.objects.create(
            service=self.svc, song_snapshot="HCC 291", song=self.song
        )
        self.song.delete()
        wss.refresh_from_db()
        self.assertIsNone(wss.song)

    def test_source_choices(self):
        self.assertIn(WorshipServiceSong.SOURCE_MANUAL, dict(WorshipServiceSong.SOURCE_CHOICES))
        self.assertIn(WorshipServiceSong.SOURCE_IMPORTED, dict(WorshipServiceSong.SOURCE_CHOICES))

    def test_resolution_choices(self):
        choices = dict(WorshipServiceSong.RESOLUTION_CHOICES)
        self.assertIn(WorshipServiceSong.RESOLUTION_LINKED, choices)
        self.assertIn(WorshipServiceSong.RESOLUTION_PENDING_REVIEW, choices)
        self.assertIn(WorshipServiceSong.RESOLUTION_UNLINKED, choices)

    def test_with_all_resolution_fields(self):
        wss = WorshipServiceSong.objects.create(
            service=self.svc,
            song_snapshot="HCC 291",
            song=self.song,
            source=WorshipServiceSong.SOURCE_IMPORTED,
            order_ref=1,
            resolution_status=WorshipServiceSong.RESOLUTION_LINKED,
            detected_hymnal_raw="HCC",
            detected_hymnal=self.hymnal,
            detected_number=291,
            match_confidence=1.0,
            resolution_note="Vinculada automaticamente.",
        )
        wss.refresh_from_db()
        self.assertEqual(wss.detected_hymnal, self.hymnal)
        self.assertEqual(wss.detected_number, 291)
        self.assertEqual(wss.resolution_note, "Vinculada automaticamente.")


class ClampFontScaleTestCase(TestCase):
    def test_clamp_within_range(self):
        from worship.views.service_views import _clamp_font_scale
        self.assertEqual(_clamp_font_scale(100), 100)

    def test_clamp_below_minimum(self):
        from worship.views.service_views import _clamp_font_scale
        self.assertEqual(_clamp_font_scale(50), 75)

    def test_clamp_above_maximum(self):
        from worship.views.service_views import _clamp_font_scale
        self.assertEqual(_clamp_font_scale(200), 130)

    def test_clamp_at_boundaries(self):
        from worship.views.service_views import _clamp_font_scale
        self.assertEqual(_clamp_font_scale(75), 75)
        self.assertEqual(_clamp_font_scale(130), 130)
