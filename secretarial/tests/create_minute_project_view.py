from django.test import TestCase
from django.urls import reverse
from secretarial.models import (
    MinuteProjectModel,
    MinuteTemplateModel,
    MinuteExcerptsModel,
    MeetingAgendaModel,
)
from users.models import CustomUser
from model_mommy import mommy
from django.contrib.auth.models import Group, Permission


class CreateMinuteProjectFormViewTestCase(TestCase):
    def setUp(self):
        # self.secretary_group = Group.objects.create(name="secretary")
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.permission = Permission.objects.get(codename="add_meetingminutemodel")
        # self.secretary_group.permissions.add(self.permission)
        # self.user.groups.add(self.secretary_group)
        self.user.user_permissions.add(self.permission)

    def test_access_non_authorized_user(self):
        url = reverse("secretarial:create-minute-project")
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 404])

    def test_template_data_initialization(self):
        self.client.login(username="testuser", password="password123")
        url = reverse("secretarial:create-minute-project")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "secretarial/minute_created.html")

    def test_context_data(self):
        self.client.login(username="testuser", password="password123")
        url = reverse("secretarial:create-minute-project")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertIn("form", response.context)
