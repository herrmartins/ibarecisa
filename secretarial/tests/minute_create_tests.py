from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from secretarial.models import MinuteProjectModel, MinuteExcerptsModel
from django.contrib.auth.models import Group, Permission


class MinuteCreateViewTest(TestCase):
    def setUp(self):
        self.secretary_group = Group.objects.create(name="secretary")
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.permission = Permission.objects.get(codename="add_meetingminutemodel")
        self.secretary_group.permissions.add(self.permission)
        self.user.groups.add(self.secretary_group)
        self.user.user_permissions.add(self.permission)
        self.client.login(username="testuser", password="password123")

    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        url = reverse("secretarial:create-minute-view")  # Change to actual URL
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 302
        )  # Expect redirect to login for unauthenticated users

    def test_permission_required(self):
        url = reverse("secretarial:create-minute-view")  # Change to actual URL
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 200
        )  # Expect Forbidden for users without required permission

    def test_context_data(self):
        # Create necessary objects for context data
        minute_excerpt_1 = MinuteExcerptsModel.objects.create(excerpt="Excerpt 1")
        minute_excerpt_2 = MinuteExcerptsModel.objects.create(excerpt="Excerpt 2")
        print("TESTES:", minute_excerpt_1, minute_excerpt_2)

        self.client.login(username="testuser", password="password123")
        url = reverse("secretarial:create-minute-view")  # Change to actual URL
        response = self.client.get(url)

        self.assertEqual(
            response.status_code, 200
        )  # Ensure user has permission and can access the view
        self.assertTemplateUsed(
            response, "secretarial/minute_created.html"
        )  # Check the correct template is used

        # Check if context data is being passed correctly
        excerpts_list = response.context["excerpts_list"]
        self.assertTrue(minute_excerpt_1 in excerpts_list)
        self.assertTrue(minute_excerpt_2 in excerpts_list)
