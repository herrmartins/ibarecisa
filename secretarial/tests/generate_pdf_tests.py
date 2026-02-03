from django.test import TestCase
from django.urls import reverse
from secretarial.models import MeetingMinuteModel
from model_bakery import baker
from django.contrib.auth.models import Group, Permission
from users.models import CustomUser


class GeneratePDFViewTestCase(TestCase):
    """
    Testes para geração de PDF usando WeasyPrint.

    Nota: Os testes antigos que mockavam render_to_pdf foram removidos
    pois a view agora usa weasyprint diretamente.
    """

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

    def test_generate_pdf_permission_required(self):
        """Test if the view requires the correct permission"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_generate_pdf_returns_pdf_content_type(self):
        """Test that the view returns a PDF content-type"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(
            f"meeting_minute_{self.meeting.pk}.pdf", response["Content-Disposition"]
        )
        # Verify that actual PDF content is returned (PDF files start with %PDF-)
        self.assertTrue(response.content.startswith(b"%PDF-"))
