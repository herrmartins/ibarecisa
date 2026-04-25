from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from worship.models import Hymnal, HymnalAlias, Song, WorshipService, WorshipServiceSong

CustomUser = get_user_model()


def _make_user(**kwargs):
    defaults = {"username": "user", "password": "pass", "type": CustomUser.Types.REGULAR}
    defaults.update(kwargs)
    return CustomUser.objects.create_user(**defaults)


class SongSyncFromProgramTestCase(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)
        self.hymnal = Hymnal.objects.create(title="CC")
        HymnalAlias.objects.create(hymnal=self.hymnal, alias="CC")
        self.song = Song.objects.create(title="A Deus demos glória", hymnal=self.hymnal, hymn_number=291)
        self.svc = WorshipService.objects.create(
            title="Culto",
            service_date=date(2026, 5, 1),
            program_html='<ol><li>CC 291 - A Deus demos glória</li><li>Oração</li><li>Hino: Vencendo vem Jesus</li></ol>',
        )

    def test_sync_extracts_hymns(self):
        response = self.client.post(
            reverse("worship:service-song-sync", kwargs={"pk": self.svc.pk})
        )
        self.assertEqual(self.svc.sung_songs.filter(source=WorshipServiceSong.SOURCE_IMPORTED).count(), 2)

    def test_sync_resolves_songs(self):
        self.client.post(reverse("worship:service-song-sync", kwargs={"pk": self.svc.pk}))
        linked = self.svc.sung_songs.filter(
            resolution_status=WorshipServiceSong.RESOLUTION_LINKED,
            song_snapshot__contains="A Deus demos glória",
        )
        self.assertEqual(linked.count(), 1)
        self.assertEqual(linked.first().song, self.song)

    def test_sync_replaces_previous_imported(self):
        WorshipServiceSong.objects.create(
            service=self.svc, song_snapshot="Old",
            source=WorshipServiceSong.SOURCE_IMPORTED,
        )
        self.client.post(reverse("worship:service-song-sync", kwargs={"pk": self.svc.pk}))
        self.assertFalse(self.svc.sung_songs.filter(song_snapshot="Old").exists())

    def test_sync_preserves_manual_songs(self):
        WorshipServiceSong.objects.create(
            service=self.svc, song_snapshot="Manual Song",
            source=WorshipServiceSong.SOURCE_MANUAL,
        )
        self.client.post(reverse("worship:service-song-sync", kwargs={"pk": self.svc.pk}))
        self.assertTrue(self.svc.sung_songs.filter(song_snapshot="Manual Song").exists())

    def test_sync_no_program_shows_warning(self):
        svc = WorshipService.objects.create(title="Vazio", service_date=date(2026, 1, 1), program_html="")
        response = self.client.post(reverse("worship:service-song-sync", kwargs={"pk": svc.pk}))
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Nenhuma" in str(m) for m in messages))


class SongAddTestCase(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(title="Culto", service_date=date(2026, 5, 1))
        self.hymnal = Hymnal.objects.create(title="CC")
        HymnalAlias.objects.create(hymnal=self.hymnal, alias="CC")
        self.song = Song.objects.create(title="A Deus demos glória", hymnal=self.hymnal, hymn_number=291)

    def test_add_song_creates_entry(self):
        response = self.client.post(
            reverse("worship:service-song-add", kwargs={"pk": self.svc.pk}),
            {"song_snapshot": "CC 291"},
        )
        self.assertEqual(self.svc.sung_songs.count(), 1)
        wss = self.svc.sung_songs.first()
        self.assertEqual(wss.source, WorshipServiceSong.SOURCE_MANUAL)
        self.assertEqual(wss.song_snapshot, "CC 291")

    def test_add_song_auto_resolves(self):
        self.client.post(
            reverse("worship:service-song-add", kwargs={"pk": self.svc.pk}),
            {"song_snapshot": "CC 291 - A Deus demos glória"},
        )
        wss = self.svc.sung_songs.first()
        self.assertEqual(wss.resolution_status, WorshipServiceSong.RESOLUTION_LINKED)
        self.assertEqual(wss.song, self.song)

    def test_add_song_order_auto_increment(self):
        WorshipServiceSong.objects.create(
            service=self.svc, song_snapshot="Hino 1", order_ref=3
        )
        self.client.post(
            reverse("worship:service-song-add", kwargs={"pk": self.svc.pk}),
            {"song_snapshot": "Hino Novo"},
        )
        wss = self.svc.sung_songs.last()
        self.assertEqual(wss.order_ref, 4)

    def test_add_song_redirects_to_detail(self):
        response = self.client.post(
            reverse("worship:service-song-add", kwargs={"pk": self.svc.pk}),
            {"song_snapshot": "Nova Canção"},
        )
        self.assertRedirects(response, reverse("worship:service-detail", kwargs={"pk": self.svc.pk}))


class SongDeleteTestCase(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(title="Culto", service_date=date(2026, 5, 1))
        self.wss = WorshipServiceSong.objects.create(
            service=self.svc, song_snapshot="Hino 1"
        )

    def test_delete_removes_entry(self):
        response = self.client.post(
            reverse("worship:service-song-delete", kwargs={"pk": self.svc.pk, "song_id": self.wss.pk})
        )
        self.assertFalse(WorshipServiceSong.objects.filter(pk=self.wss.pk).exists())
        self.assertRedirects(response, reverse("worship:service-detail", kwargs={"pk": self.svc.pk}))

    def test_delete_wrong_service_404(self):
        svc2 = WorshipService.objects.create(title="Outro", service_date=date(2026, 6, 1))
        response = self.client.post(
            reverse("worship:service-song-delete", kwargs={"pk": svc2.pk, "song_id": self.wss.pk})
        )
        self.assertEqual(response.status_code, 404)


class SongResolveLinkTestCase(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(title="Culto", service_date=date(2026, 5, 1))
        self.song = baker.make(Song, title="A Deus demos glória")
        self.wss = WorshipServiceSong.objects.create(
            service=self.svc,
            song_snapshot="CC 291",
            resolution_status=WorshipServiceSong.RESOLUTION_PENDING_REVIEW,
        )

    def test_link_action(self):
        response = self.client.post(
            reverse("worship:service-song-resolve", kwargs={"pk": self.svc.pk, "song_id": self.wss.pk}),
            {"action": "link", "song": self.song.pk},
        )
        self.wss.refresh_from_db()
        self.assertEqual(self.wss.song, self.song)
        self.assertEqual(self.wss.resolution_status, WorshipServiceSong.RESOLUTION_LINKED)
        self.assertEqual(self.wss.match_confidence, 1)

    def test_link_without_song_shows_error(self):
        response = self.client.post(
            reverse("worship:service-song-resolve", kwargs={"pk": self.svc.pk, "song_id": self.wss.pk}),
            {"action": "link", "song": ""},
        )
        self.wss.refresh_from_db()
        self.assertEqual(self.wss.resolution_status, WorshipServiceSong.RESOLUTION_PENDING_REVIEW)

    def test_link_with_invalid_song_404(self):
        response = self.client.post(
            reverse("worship:service-song-resolve", kwargs={"pk": self.svc.pk, "song_id": self.wss.pk}),
            {"action": "link", "song": 99999},
        )
        self.assertEqual(response.status_code, 404)

    def test_link_can_change_existing(self):
        self.wss.song = self.song
        self.wss.resolution_status = WorshipServiceSong.RESOLUTION_LINKED
        self.wss.save()
        new_song = baker.make(Song, title="Outra Canção")
        self.client.post(
            reverse("worship:service-song-resolve", kwargs={"pk": self.svc.pk, "song_id": self.wss.pk}),
            {"action": "link", "song": new_song.pk},
        )
        self.wss.refresh_from_db()
        self.assertEqual(self.wss.song, new_song)


class SongResolveUnlinkTestCase(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(title="Culto", service_date=date(2026, 5, 1))
        self.hymnal = Hymnal.objects.create(title="HCC")
        self.song = baker.make(Song, title="Hino")
        self.wss = WorshipServiceSong.objects.create(
            service=self.svc,
            song_snapshot="HCC 100",
            song=self.song,
            resolution_status=WorshipServiceSong.RESOLUTION_LINKED,
            detected_hymnal=self.hymnal,
            detected_number=100,
        )

    def test_unlink_action(self):
        response = self.client.post(
            reverse("worship:service-song-resolve", kwargs={"pk": self.svc.pk, "song_id": self.wss.pk}),
            {"action": "unlink"},
        )
        self.wss.refresh_from_db()
        self.assertIsNone(self.wss.song)
        self.assertEqual(self.wss.resolution_status, WorshipServiceSong.RESOLUTION_UNLINKED)
        self.assertIn("Mantida avulsa", self.wss.resolution_note)

    def test_unlink_note_includes_hymnal(self):
        self.client.post(
            reverse("worship:service-song-resolve", kwargs={"pk": self.svc.pk, "song_id": self.wss.pk}),
            {"action": "unlink"},
        )
        self.wss.refresh_from_db()
        self.assertIn("HCC", self.wss.resolution_note)
        self.assertIn("100", self.wss.resolution_note)


class SongResolveRetryTestCase(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)
        self.svc = WorshipService.objects.create(title="Culto", service_date=date(2026, 5, 1))
        self.wss = WorshipServiceSong.objects.create(
            service=self.svc,
            song_snapshot="CC 291",
            resolution_status=WorshipServiceSong.RESOLUTION_PENDING_REVIEW,
        )

    @patch("worship.views.service_views.resolve_song_reference")
    def test_retry_updates_resolution(self, mock_resolve):
        song_obj = baker.make(Song, title="A Deus demos glória")
        mock_resolve.return_value = {
            "song": song_obj,
            "resolution_status": WorshipServiceSong.RESOLUTION_LINKED,
            "detected_hymnal_raw": "CC",
            "detected_hymnal": None,
            "detected_number": 291,
            "match_confidence": "0.950",
            "resolution_note": "Vinculada.",
        }
        self.client.post(
            reverse("worship:service-song-resolve", kwargs={"pk": self.svc.pk, "song_id": self.wss.pk}),
            {"action": "retry"},
        )
        self.wss.refresh_from_db()
        self.assertEqual(self.wss.song, song_obj)
        self.assertEqual(self.wss.resolution_status, WorshipServiceSong.RESOLUTION_LINKED)
        self.assertIsNotNone(self.wss.match_confidence)

    def test_invalid_action_shows_error(self):
        response = self.client.post(
            reverse("worship:service-song-resolve", kwargs={"pk": self.svc.pk, "song_id": self.wss.pk}),
            {"action": "invalid"},
        )
        self.wss.refresh_from_db()
        self.assertEqual(self.wss.resolution_status, WorshipServiceSong.RESOLUTION_PENDING_REVIEW)
