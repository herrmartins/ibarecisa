from django.test import TestCase
from users.models import CustomUser
from events.models import Event, Venue, EventCategory
from events.forms import EventForm
from model_mommy import mommy


class EventFormTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(
            username="testuser", email="test@example.com"
        )
        self.location = mommy.make(Venue)
        mommy.make(EventCategory, _quantity=5)

        self.valid_data = {
            "user": self.user.id,
            "title": "Sample Event",
            "description": "A description for the event.",
            "start_date": "2025-01-01 12:00:00",
            "end_date": "2025-01-01 14:00:00",
            "price": "10.00",
            "location": self.location.id,
            "contact_user": "",
            "contact_name": "John Doe",
            "category": 2,
        }

    def test_event_form_valid(self):
        form = EventForm(data=self.valid_data, user=self.user)
        self.assertTrue(form.is_valid(), form.errors.as_text())

    def test_event_form_invalid_contact_info(self):
        invalid_data = self.valid_data.copy()
        del invalid_data["start_date"]
        form = EventForm(data=invalid_data, user=self.user)
        self.assertFalse(form.is_valid(), form.errors.as_text())
        self.assertIn("start_date", form.errors)
        self.assertEqual(
            form.errors["start_date"],
            ["Este campo é obrigatório."],
        )

    def test_event_form_invalid_user_does_not_exist(self):
        invalid_data = self.valid_data.copy()
        invalid_data["contact_name"] = None
        form = EventForm(data=invalid_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("contact_name", form.errors)
        self.assertEqual(form.errors["contact_name"], ["Please provide contact information."])
