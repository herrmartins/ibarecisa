from django.test import TestCase
from django.urls import reverse
from users.forms import LoginForm


class IndexViewTests(TestCase):
    def test_index_view_uses_correct_template(self):
        response = self.client.get(
            reverse("core:home")
        )  # Assuming 'index' is the URL name for IndexView
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/index.html")

    def test_index_view_context_contains_login_form(self):
        response = self.client.get(
            reverse("core:home")
        )  # Assuming 'index' is the URL name for IndexView
        self.assertIn("login_form", response.context)
        self.assertIsInstance(response.context["login_form"], LoginForm)
