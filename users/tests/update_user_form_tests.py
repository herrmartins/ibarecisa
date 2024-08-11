from django.test import TestCase
from users.forms import UpdateUserProfileModelForm


class UpdateUserProfileFormTest(TestCase):
    def test_update_user_profile_blank_data(self):
        # Test with blank form data
        # Provide a valid email address
        form = UpdateUserProfileModelForm(data={"email": "test@example.com"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_update_user_profile_wrong_date_format(self):
        # Test with wrong date format
        form = UpdateUserProfileModelForm(data={"date_of_birth": "07-06-1986"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["date_of_birth"], ["Informe uma data válida."])

    def test_valid_date_format(self):
        form = UpdateUserProfileModelForm(
            data={"date_of_birth": "1986-07-06", "email": "test@example.com"}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        # Test with missing email and any other required fields
        form = UpdateUserProfileModelForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        # Include assertions for other required fields

    def test_valid_form_data(self):
        valid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "address": "123 Main St",
            "phone_number": "1234567890",
            "is_whatsapp": False,
            "date_of_birth": "1986-07-06",
            "about": "Some description",
        }
        form = UpdateUserProfileModelForm(data=valid_data)
        self.assertTrue(form.is_valid())
