from django.test import TestCase
from django.urls import reverse
from secretarial.models import (
    MinuteProjectModel,
    MinuteTemplateModel,
    MinuteExcerptsModel,
    MeetingAgendaModel,
)
from users.models import CustomUser
from model_bakery import baker
from django.contrib.auth.models import Group, Permission


class CreateMinuteFormViewTestCase(TestCase):
    def setUp(self):
        self.secretary_group = Group.objects.create(name="secretary")
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.permission = Permission.objects.get(codename="add_meetingminutemodel")
        self.secretary_group.permissions.add(self.permission)
        self.user.groups.add(self.secretary_group)
        self.user.user_permissions.add(self.permission)
        self.client.login(username="testuser", password="password123")

    def test_project_data_initialization(self):
        # Create a MinuteProjectModel for testing
        project = baker.make(MinuteProjectModel, number_of_attendees=50)

        url = reverse(
            "secretarial:minute-creation-form-view", kwargs={"project_pk": project.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Add more assertions based on expected behavior after fetching project data

    def test_template_data_initialization(self):
        # Create a MinuteTemplateModel for testing
        template = baker.make(MinuteTemplateModel)
        url = reverse(
            "secretarial:minute-from-template-view", kwargs={"template_pk": template.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        project = baker.make(MinuteProjectModel)
        baker.make(MinuteExcerptsModel, _quantity=5)
        url = reverse(
            "secretarial:minute-creation-form-view", kwargs={"project_pk": project.pk}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertIn("excerpts_list", response.context)

    def test_get_initial_with_project_pk(self):
        # Agora eu mudei pra ter acesso, então o teste perdeu o sentido
        # url_with_non_existing_project = reverse(
        #     "secretarial:minute-creation-form-view",
        #     kwargs={"project_pk": 5845},
        # )
        # response_with_project = self.client.get(url_with_non_existing_project)
        # self.assertIn(response_with_project.status_code, [302, 404])

        president = baker.make(CustomUser, first_name="Sample President")
        secretary = baker.make(CustomUser, first_name="Sample Secretary")

        project_with_data = baker.make(
            MinuteProjectModel,
            president=president,
            secretary=secretary,
            body="Sample Body",
        )
        project_with_data.meeting_agenda.set(baker.make(MeetingAgendaModel, _quantity=2))

        url_with_existing_project = reverse(
            "secretarial:minute-creation-form-view",
            kwargs={"project_pk": project_with_data.pk},
        )
        response_with_project = self.client.get(url_with_existing_project)

        self.assertEqual(response_with_project.status_code, 200)

        initial_data = response_with_project.context["form"].initial
        expected_meeting_date_str = project_with_data.meeting_date.strftime("%Y-%m-%d")
        expected_number_of_atendees = project_with_data.number_of_attendees

        self.assertIn("president", initial_data)
        self.assertEqual(initial_data["president"].first_name, "Sample President")
        self.assertIn("secretary", initial_data)
        self.assertEqual(initial_data["secretary"].first_name, "Sample Secretary")
        self.assertIn("meeting_date", initial_data)
        self.assertEqual(initial_data["meeting_date"], expected_meeting_date_str)
        self.assertIn("number_of_attendees", initial_data)
        self.assertEqual(
            initial_data["number_of_attendees"], expected_number_of_atendees
        )
        self.assertIn("meeting_date", initial_data)
        self.assertEqual(initial_data["body"], project_with_data.body)
        self.assertIn("agenda", initial_data)

    def test_get_initial_with_template_pk(self):
        # Create a template with specific data for testing using Model Mommy (agora Baker)
        template_with_data = baker.make(MinuteTemplateModel)

        # Get the URL with the created template's PK
        url_with_existing_template = reverse(
            "secretarial:minute-from-template-view",
            kwargs={"template_pk": template_with_data.pk},
        )
        response_with_existing_template = self.client.get(url_with_existing_template)

        initial_data = response_with_existing_template.context["form"].initial

        # Check if the view renders successfully
        self.assertEqual(response_with_existing_template.status_code, 200)
        self.assertEqual(initial_data["body"], template_with_data.body)
        self.assertIn("agenda", initial_data)
