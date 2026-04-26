from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from worship.models import Composer, Hymnal, Song, SongTheme

CustomUser = get_user_model()


def _make_user(**kwargs):
    defaults = {"username": "user", "password": "pass", "type": CustomUser.Types.REGULAR}
    defaults.update(kwargs)
    return CustomUser.objects.create_user(**defaults)


class SongListViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)
        self.composer = Composer.objects.create(name="Charles Wesley")
        self.theme = SongTheme.objects.create(title="Natal")
        self.hymnal = Hymnal.objects.create(title="HCC")
        self.song1 = Song.objects.create(
            title="A Deus demos glória",
            artist=self.composer,
            hymnal=self.hymnal,
            hymn_number=291,
        )
        self.song1.themes.add(self.theme)
        self.song2 = Song.objects.create(title="Vencendo vem Jesus")

    def test_list_returns_200(self):
        response = self.client.get(reverse("worship:song-list"))
        self.assertEqual(response.status_code, 200)

    def test_list_shows_all_songs(self):
        response = self.client.get(reverse("worship:song-list"))
        self.assertEqual(len(response.context["songs"]), 2)

    def test_list_ordered_by_title(self):
        response = self.client.get(reverse("worship:song-list"))
        titles = [s.title for s in response.context["songs"]]
        self.assertEqual(titles, sorted(titles))

    def test_filter_by_title(self):
        response = self.client.get(reverse("worship:song-list") + "?q=glória")
        self.assertEqual(len(response.context["songs"]), 1)
        self.assertEqual(response.context["songs"][0].title, "A Deus demos glória")

    def test_filter_by_composer(self):
        response = self.client.get(reverse("worship:song-list") + f"?composer={self.composer.pk}")
        self.assertEqual(len(response.context["songs"]), 1)

    def test_filter_by_theme(self):
        response = self.client.get(reverse("worship:song-list") + f"?theme={self.theme.pk}")
        self.assertEqual(len(response.context["songs"]), 1)

    def test_filter_by_hymnal(self):
        response = self.client.get(reverse("worship:song-list") + f"?hymnal={self.hymnal.pk}")
        self.assertEqual(len(response.context["songs"]), 1)

    def test_combined_filters(self):
        response = self.client.get(
            reverse("worship:song-list")
            + f"?q=glória&composer={self.composer.pk}&hymnal={self.hymnal.pk}"
        )
        self.assertEqual(len(response.context["songs"]), 1)

    def test_filter_no_results(self):
        response = self.client.get(reverse("worship:song-list") + "?q=ZZZZZ")
        self.assertEqual(len(response.context["songs"]), 0)

    def test_context_has_filter_options(self):
        response = self.client.get(reverse("worship:song-list"))
        self.assertIn("composers", response.context)
        self.assertIn("themes", response.context)
        self.assertIn("hymnals", response.context)
        self.assertIn("filters", response.context)

    def test_not_authenticated_redirects(self):
        self.client.logout()
        response = self.client.get(reverse("worship:song-list"))
        self.assertEqual(response.status_code, 302)


class SongCreateViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)

    def test_create_get(self):
        response = self.client.get(reverse("worship:song-create"))
        self.assertEqual(response.status_code, 200)

    def test_create_post_valid(self):
        response = self.client.post(reverse("worship:song-create"), {
            "title": "Nova Canção",
            "artist": "",
            "themes": [],
            "hymnal": "",
            "hymn_number": "",
            "key": "",
            "metrics": "",
            "lyrics": "",
        })
        song = Song.objects.first()
        self.assertIsNotNone(song)
        self.assertEqual(song.title, "Nova Canção")
        self.assertRedirects(response, reverse("worship:song-detail", kwargs={"pk": song.pk}))

    def test_create_without_title_invalid(self):
        response = self.client.post(reverse("worship:song-create"), {
            "title": "",
            "artist": "",
            "themes": [],
            "hymnal": "",
            "hymn_number": "",
            "key": "",
            "metrics": "",
            "lyrics": "",
        })
        self.assertEqual(Song.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_create_with_all_fields(self):
        composer = Composer.objects.create(name="Wesley")
        hymnal = Hymnal.objects.create(title="HCC")
        theme = SongTheme.objects.create(title="Graça")
        response = self.client.post(reverse("worship:song-create"), {
            "title": "Canção Completa",
            "artist": composer.pk,
            "themes": [theme.pk],
            "hymnal": hymnal.pk,
            "hymn_number": 100,
            "key": "G",
            "metrics": "8.7.8.7",
            "lyrics": "<p>Letra aqui</p>",
        })
        song = Song.objects.first()
        self.assertIsNotNone(song)
        self.assertEqual(song.artist, composer)
        self.assertEqual(song.hymnal, hymnal)
        self.assertEqual(song.hymn_number, 100)
        self.assertEqual(song.key, "G")
        self.assertIn(theme, song.themes.all())
