from django.test import TestCase, override_settings
from users.forms.user_registration_form import RegisterUserForm


@override_settings(AUTH_PASSWORD_VALIDATORS=[], CAPTCHA_TEST_MODE=True)
class RegisterUserFormTest(TestCase):

    def test_form_valid_with_required_fields(self):
        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@example.com',
            'password1': 'password123',
            'password2': 'password123',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_without_required_fields(self):
        form_data = {
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@example.com',
            'password1': 'conundrum123456789!',
            'password2': 'conundrum123456789!',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

        form_data = {
            'username': 'testuser',
            'last_name': 'Silva',
            'email': 'joao@example.com',
            'password1': 'MySecurePass123!',
            'password2': 'MySecurePass123!',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'email': 'joao@example.com',
            'password1': 'MySecurePass123!',
            'password2': 'MySecurePass123!',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)

        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
            'password1': 'conundrum123456789!',
            'password2': 'conundrum123456789!',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@example.com',
            'password2': 'password123',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)

        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@example.com',
            'password1': 'password123',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_password_validation(self):

        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@example.com',
            'password1': 'password123',
            'password2': 'password456',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@example.com',
            'password1': '123',
            'password2': '123',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_email_validation(self):
        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'invalid-email',
            'password1': 'password123',
            'password2': 'password123',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@example.com',
            'password1': 'password123',
            'password2': 'password123',
            'captcha_0': 'dummy',
            'captcha_1': 'PASSED',
        }
        form = RegisterUserForm(data=form_data)
        self.assertTrue(form.is_valid())