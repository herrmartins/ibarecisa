from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser


class UsersQualifyingListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.regular_user = CustomUser.objects.create(
            username='regular_user', email='regular_user_qualify@example.com',
            type=CustomUser.Types.REGULAR
        )
        cls.staff_user = CustomUser.objects.create(
            username='staff_user', email='staff_user_qualify@example.com',
            type=CustomUser.Types.STAFF
        )
        cls.admin_user = CustomUser.objects.create(
            username='admin_user', email='admin_user_qualify@example.com',
            is_superuser=True
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('secretarial:users-qualifying'))
        self.assertEqual(response.status_code, 302)

    def test_view_url_accessible_by_permission(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('secretarial:users-qualifying'))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('secretarial:users-qualifying'))
        self.assertIn('members', response.context)
        self.assertIn('users', response.context)
