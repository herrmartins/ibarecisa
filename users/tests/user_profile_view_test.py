from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser
from django.contrib.auth.models import User
from django.test.client import Client
from users.views import UserProfileView
from model_bakery import baker


class UserProfileViewTest(TestCase):
    def setUp(self):
        self.custom_user = CustomUser.objects.create_user(
            username="testuser", password="password"
        )
        self.client = Client()

    def test_user_profile_view_with_permission(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get(
            reverse("users:user-profile", kwargs={"pk": self.custom_user.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/user_profile.html")
        self.assertEqual(response.context["user_object"], self.custom_user)

    def test_user_profile_view_without_permission(self):
        CustomUser.objects.create_user(username="otheruser", password="password")
        baker.make('CustomUser')
        self.client.login(username="otheruser", password="password")
        response = self.client.get(
            reverse("users:user-profile", kwargs={"pk": self.custom_user.pk})
        )
        self.assertEqual(
            response.status_code, 403
        )

    def test_get_object(self):
        view = UserProfileView()
        view.kwargs = {"pk": self.custom_user.pk}
        obj = view.get_object()
        self.assertEqual(obj, self.custom_user)

    def test_has_permission(self):
        view = UserProfileView()
        view.request = self.client.get("/")
        view.request.user = self.custom_user
        view.kwargs = {"pk": self.custom_user.pk}
        has_permission = view.has_permission()
        self.assertTrue(has_permission)
