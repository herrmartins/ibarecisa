from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from worship.models import Composer, Hymnal, SongTheme

CustomUser = get_user_model()


def _make_user(**kwargs):
    defaults = {"username": "user", "password": "pass", "type": CustomUser.Types.REGULAR}
    defaults.update(kwargs)
    return CustomUser.objects.create_user(**defaults)


class CatalogSettingsViewTestCase(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.client.force_login(self.user)

    def test_get_returns_200(self):
        response = self.client.get(reverse("worship:catalog-settings"))
        self.assertEqual(response.status_code, 200)

    def test_context_has_forms(self):
        response = self.client.get(reverse("worship:catalog-settings"))
        self.assertIn("composer_form", response.context)
        self.assertIn("hymnal_form", response.context)
        self.assertIn("theme_form", response.context)

    def test_context_has_recent_items(self):
        baker.make(Composer, _quantity=3)
        baker.make(Hymnal, _quantity=3)
        baker.make(SongTheme, _quantity=5)
        response = self.client.get(reverse("worship:catalog-settings"))
        self.assertEqual(len(response.context["recent_composers"]), 3)
        self.assertEqual(len(response.context["recent_hymnals"]), 3)
        self.assertEqual(len(response.context["recent_themes"]), 5)

    def test_add_composer(self):
        response = self.client.post(
            reverse("worship:catalog-settings"),
            {"action": "add_composer", "name": "Charles Wesley", "bio": "Hymn writer"},
        )
        self.assertEqual(Composer.objects.count(), 1)
        self.assertEqual(Composer.objects.first().name, "Charles Wesley")
        self.assertRedirects(response, reverse("worship:catalog-settings"))

    def test_add_composer_invalid(self):
        response = self.client.post(
            reverse("worship:catalog-settings"),
            {"action": "add_composer", "name": "", "bio": ""},
        )
        self.assertEqual(Composer.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_add_hymnal(self):
        response = self.client.post(
            reverse("worship:catalog-settings"),
            {"action": "add_hymnal", "title": "Hinário Novo", "author": "", "edition": ""},
        )
        self.assertEqual(Hymnal.objects.count(), 1)
        self.assertEqual(Hymnal.objects.first().title, "Hinário Novo")

    def test_add_hymnal_invalid(self):
        response = self.client.post(
            reverse("worship:catalog-settings"),
            {"action": "add_hymnal", "title": "", "author": "", "edition": ""},
        )
        self.assertEqual(Hymnal.objects.count(), 0)

    def test_add_theme(self):
        response = self.client.post(
            reverse("worship:catalog-settings"),
            {"action": "add_theme", "title": "Natal"},
        )
        self.assertEqual(SongTheme.objects.count(), 1)
        self.assertEqual(SongTheme.objects.first().title, "Natal")

    def test_add_theme_invalid(self):
        response = self.client.post(
            reverse("worship:catalog-settings"),
            {"action": "add_theme", "title": ""},
        )
        self.assertEqual(SongTheme.objects.count(), 0)

    def test_invalid_action(self):
        response = self.client.post(
            reverse("worship:catalog-settings"),
            {"action": "invalid"},
        )
        self.assertRedirects(response, reverse("worship:catalog-settings"))

    def test_not_authenticated_redirects(self):
        self.client.logout()
        response = self.client.get(reverse("worship:catalog-settings"))
        self.assertEqual(response.status_code, 302)
