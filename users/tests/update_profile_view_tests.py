from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import CustomUser
from users.forms import UpdateUserProfileModelForm
from django.urls import reverse
from django.contrib.auth.models import Group, Permission


class UserProfileUpdateViewTestAsSecretary(TestCase):
    def setUp(self):
        self.secretary_group = Group.objects.create(name="secretary")
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.user_to_update = get_user_model().objects.create_user(
            username="updateuser", email="update@example.com", password="updatepass123"
        )
        self.permission = Permission.objects.get(codename="change_customuser")
        self.secretary_group.permissions.add(self.permission)
        self.user.groups.add(self.secretary_group)
        self.user.user_permissions.add(self.permission)
        self.client.login(username="testuser", password="password123")

    def test_user_profile_update_view(self):
        url = reverse(
            "users:user-profile-update", kwargs={"pk": self.user_to_update.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/user_profile_update_form.html")

    def test_user_profile_update_view_form(self):
        url = reverse('users:user-profile-update', kwargs={'pk': self.user_to_update.pk})
        response = self.client.get(url)
        form = response.context['form']
        self.assertIsInstance(form, UpdateUserProfileModelForm)

    def test_user_profile_update_permission(self):
        # WARNING: logout
        self.client.logout()
        url = reverse('users:user-profile-update', kwargs={'pk': self.user_to_update.pk})
        response = self.client.get(url)
        # It's not 403, it redirects to the login
        self.assertEqual(response.status_code, 302)

    def test_user_profile_update_permission_own_user(self):
        url = reverse('users:user-profile-update', kwargs={'pk': self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class UserProfileUpdateViewTestAsTreasurer(TestCase):
    def setUp(self):
        self.secretary_group = Group.objects.create(name="treasury")
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.user_to_update = get_user_model().objects.create_user(
            username="updateuser", email="update@example.com", password="updatepass123"
        )
        self.permission = Permission.objects.get(codename="change_customuser")
        self.secretary_group.permissions.add(self.permission)
        self.user.groups.add(self.secretary_group)
        self.user.user_permissions.add(self.permission)
        self.client.login(username="testuser", password="password123")

    def test_user_profile_update_view(self):
        url = reverse(
            "users:user-profile-update", kwargs={"pk": self.user_to_update.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "users/user_profile_update_form.html")

    def test_user_profile_update_permission(self):
        self.client.logout()
        url = reverse('users:user-profile-update', kwargs={'pk': self.user_to_update.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_user_profile_update_permission_own_user(self):
        url = reverse('users:user-profile-update', kwargs={'pk': self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)