from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from users.models import CustomUser
from secretarial.models import (
    MeetingMinuteModel,
    MinuteProjectModel,
    MinuteExcerptsModel,
    MinuteTemplateModel,
)
from secretarial.forms import MinuteProjectModelForm
from model_mommy import mommy


class MinuteHomeViewTest(TestCase):
    def setUp(self):
        self.secretary_group = Group.objects.create(name="secretary")
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.permission = Permission.objects.get(codename="view_meetingminutemodel")
        self.secretary_group.permissions.add(self.permission)
        self.user.groups.add(self.secretary_group)
        self.user.user_permissions.add(self.permission)

    def test_view_requires_permissions(self):
        # Ensure the view requires the correct permissions to access
        response = self.client.get(reverse("secretarial:minute-home"))
        self.assertEqual(response.status_code, 302)  # Redirects if permission denied

        # Login the test user
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("secretarial:minute-home"))
        self.assertEqual(response.status_code, 200)  # Should be accessible now

        # self.assertContains(response, "Some content in the response")

    def test_view_context_data(self):
        # Test if the context data is being set correctly in the view
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("secretarial:minute-home"))

        mommy.make(MeetingMinuteModel, _quantity=5)
        mommy.make(MinuteProjectModel, _quantity=5)
        mommy.make(MinuteTemplateModel, _quantity=5)
        mommy.make(MinuteExcerptsModel, _quantity=5)

        self.assertTrue("form" in response.context)
        self.assertIsInstance(response.context["form"], MinuteProjectModelForm)
        self.assertTrue("meeting_minutes" in response.context)
        self.assertTrue("number_of_projects" in response.context)

        self.assertEqual(len(response.context["meeting_minutes"]), 5)
        #self.assertEqual(response.context["number_of_projects"], 5)
        self.assertEqual(response.context["number_of_templates"], 5)
        self.assertEqual(response.context["number_of_excerpts"], 5)
        self.assertEqual(len(response.context["minutes"]), 5)

    def test_get_context_data(self):
        # Creating test instances using Model Mommy
        mommy.make(MeetingMinuteModel, _quantity=5)
        mommy.make(MinuteProjectModel, _quantity=3)
        mommy.make(MinuteExcerptsModel, _quantity=7)
        mommy.make(MinuteTemplateModel, _quantity=4)

        try:
            # Check if the context is generated properly and not None
            self.client.login(username="testuser", password="password123")
            response = self.client.get(reverse("secretarial:minute-home"))
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.context)

            # Check if the context contains the expected keys
            self.assertIn("form", response.context)
            self.assertIn("meeting_minutes", response.context)
            self.assertIn("number_of_projects", response.context)
            self.assertIn("number_of_excerpts", response.context)
            self.assertIn("number_of_minutes", response.context)
            self.assertIn("minutes", response.context)
            self.assertIn("number_of_templates", response.context)

            # Check if the context values are as expected
            self.assertIsInstance(response.context["form"], MinuteProjectModelForm)
            self.assertEqual(len(response.context["meeting_minutes"]), 5)
            self.assertEqual(response.context["number_of_projects"], 3)
            self.assertEqual(response.context["number_of_excerpts"], 7)
            # Add more assertions for other context data as needed

        except Exception as e:
            # Print the exception for debugging
            print(f"Erro ocorrido: {e}")
            raise e
