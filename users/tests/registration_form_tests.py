from django.test import TestCase
from django.contrib.auth import get_user_model
from users.forms import RegisterUserForm


class RegisterUserFormTest(TestCase):
    def test_register_user_form_valid(self):
        # Create a valid form data dictionary
        form_data = {
            "username": "testuser",
            "first_name": "John",
            "last_name": "Doe",
            "email":"john@doeinc.com",
            "password1": "testpassword123",
            "password2": "testpassword123",
        }

        form = RegisterUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_register_user_form_invalid(self):
        # Create an invalid form data dictionary (passwords don't match)
        form_data = {
            "username": "testuser",
            "first_name": "John",
            "last_name": "Doe",
            "email":"john@doeinc.com",
            "password1": "testpassword123",
            "password2": "differentpassword",
        }

        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_register_user_form_blank_data(self):
        # Test with blank form data
        form = RegisterUserForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['username'], ['Este campo é obrigatório.'])
        self.assertEqual(form.errors['email'], ['Este campo é obrigatório.'])
        self.assertEqual(form.errors['password1'], ['Este campo é obrigatório.'])
        self.assertEqual(form.errors['password2'], ['Este campo é obrigatório.'])
