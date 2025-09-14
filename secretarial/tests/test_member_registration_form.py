import uuid

from django.test import TestCase
from django.contrib.auth import get_user_model
from secretarial.forms.member_registration_form import MemberRegistrationForm

CustomUser = get_user_model()


class MemberRegistrationFormTest(TestCase):

    def test_form_valid_with_minimum_data(self):
        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_without_required_fields(self):
        form_data = {
            'first_name': 'João',
            'last_name': 'Silva',
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

        form_data = {
            'username': 'testuser',
            'last_name': 'Silva',
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

        form_data = {
            'username': 'testuser',
            'first_name': 'João',
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)

    def test_form_valid_with_all_fields(self):
        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@example.com',
            'date_of_birth': '1990-01-01',
            'phone_number': '+5511999999999',
            'cpf': '123.456.789-00',
            'baptism_date': '2020-01-01',
            'address': 'Rua Teste, 123',
            'about': 'Sobre o membro',
            'type': CustomUser.Types.REGULAR,
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())


    def test_form_save_without_password(self):
        form_data = {
            'username': 'testuser',
            'first_name': 'João',
            'last_name': 'Silva',
            'type': CustomUser.Types.REGULAR,
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.first_name, 'João')
        self.assertEqual(user.last_name, 'Silva')
        self.assertEqual(user.type, CustomUser.Types.REGULAR)
        self.assertFalse(user.has_usable_password())

    def test_form_save_generates_fictitious_email_when_none_provided(self):
        form_data = {
            'username': 'testuser_no_email',
            'first_name': 'João',
            'last_name': 'Silva',
            'type': CustomUser.Types.REGULAR,
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.username, 'testuser_no_email')
        self.assertTrue(user.email.startswith('no-email+'))
        self.assertTrue(user.email.endswith('@example.com'))
        self.assertEqual(len(user.email), len('no-email+') + 32 + len('@example.com'))  # uuid.hex is 32 chars
        self.assertFalse(user.has_usable_password())
