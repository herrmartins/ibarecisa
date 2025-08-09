from django.test import TestCase
from django.urls import reverse
from secretarial.models import MeetingMinuteModel
from unittest.mock import patch
from secretarial.utils.topdfutils import render_to_pdf
from model_bakery import baker
from django.contrib.auth.models import Group, Permission
from users.models import CustomUser


class GeneratePDFViewTestCase(TestCase):
    def setUp(self):
        self.secretary_group = Group.objects.create(name="secretary")
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.permission = Permission.objects.get(codename="view_meetingminutemodel")
        self.secretary_group.permissions.add(self.permission)
        self.user.groups.add(self.secretary_group)
        self.user.user_permissions.add(self.permission)
        self.client.login(username="testuser", password="password123")
        self.meeting = baker.make("secretarial.MeetingMinuteModel")
        self.url = reverse(
            "secretarial:minute-generate-pdf", kwargs={"pk": self.meeting.pk}
        )

    @patch("secretarial.utils.topdfutils.render_to_pdf")
    def test_generate_pdf_success(self, mock_render_to_pdf):
        # Mock render_to_pdf to return a PDF content
        pdf_content = b"Mock PDF Content"
        mock_render_to_pdf.return_value = pdf_content

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(
            f"meeting_minute_{self.meeting.pk}.pdf", response["Content-Disposition"]
        )
        self.assertEqual(response.content, pdf_content)

    @patch("secretarial.utils.topdfutils.render_to_pdf")
    def test_generate_pdf_failure(self, mock_render_to_pdf):
        # Mock render_to_pdf to return None (failure scenario)
        mock_render_to_pdf.return_value = None

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Failed to generate PDF.")

    def test_generate_pdf_permission_required(self):
        # Test if the view requires the correct permission
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302 or 403)
