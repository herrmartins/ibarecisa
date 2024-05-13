from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.models import Group
from users.models import CustomUser
from django.db.models.signals import post_save
from django.test.utils import override_settings


class CustomUserTestCase(TestCase):
    def setUp(self):
        self.regular_group = Group.objects.create(name="members")
        self.user_regular = CustomUser.objects.create(username="user_regular")
        self.user_regular.groups.add(self.regular_group)

    def test_user_creation(self):
        expected_count = 1
        self.assertEqual(CustomUser.objects.count(), expected_count)

    def test_user_groups(self):
        regular_group = Group.objects.get(name="members")
        # Test if the user is assigned to the regular group upon creation
        self.assertTrue(regular_group in self.user_regular.groups.all())

    def test_user_assigned_to_group(self):
        unique_username = "unique_user_test"
        # Create a user and associate it with the 'members' group
        user_regular = CustomUser.objects.create(username=unique_username)
        user_regular.groups.add(self.regular_group)

        # Retrieve the 'members' group
        regular_group = Group.objects.get(name="members")

        # Check if the user is in the 'members' group
        self.assertTrue(regular_group in user_regular.groups.all())

    def test_user_type_logic(self):
        pass

    def test_user_absolute_url(self):
        url = self.user_regular.get_absolute_url()
        self.assertEqual(
            url, reverse("users:user-profile", kwargs={"pk": str(self.user_regular.pk)})
        )

    @override_settings(DEBUG=True)
    def test_signal_handling(self):
        user = CustomUser.objects.create(username="test_user")
        users_group = Group.objects.get(name="users")

        self.assertTrue(users_group in user.groups.all())

        self.assertEqual(user.type, CustomUser.Types.SIMPLE_USER)
        self.assertFalse(user.is_pastor)
        self.assertFalse(user.is_secretary)
        self.assertFalse(user.is_treasurer)

        user.type = CustomUser.Types.REGULAR
        user.save()

        self.assertEqual(user.type, CustomUser.Types.REGULAR)
        self.assertFalse(user.is_pastor)
        self.assertFalse(user.is_secretary)
        self.assertFalse(user.is_treasurer)

        user.type = CustomUser.Types.STAFF
        user.save()

        self.assertEqual(user.type, CustomUser.Types.REGULAR)
        self.assertFalse(user.is_pastor)
        self.assertFalse(user.is_secretary)
        self.assertFalse(user.is_treasurer)

    def test_pastor_only(self):
        user = CustomUser.objects.create(username="test_user")
        user.type = CustomUser.Types.STAFF
        user.is_pastor = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.STAFF)
        self.assertTrue(user.is_pastor)
        self.assertFalse(user.is_secretary)
        self.assertFalse(user.is_treasurer)

        user.type = CustomUser.Types.REGULAR
        user.save()

        self.assertEqual(user.type, CustomUser.Types.STAFF)
        self.assertTrue(user.is_pastor)
        self.assertFalse(user.is_secretary)
        self.assertFalse(user.is_treasurer)

    def test_pastor_and_secretary(self):
        user = CustomUser.objects.create(username="test_user")
        user.type = CustomUser.Types.STAFF
        user.is_pastor = True
        user.is_secretary = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.STAFF)
        self.assertTrue(user.is_pastor)
        self.assertTrue(user.is_secretary)
        self.assertFalse(user.is_treasurer)

        user.type = CustomUser.Types.REGULAR
        user.save()

        self.assertEqual(user.type, CustomUser.Types.STAFF)
        self.assertTrue(user.is_pastor)
        self.assertTrue(user.is_secretary)
        self.assertFalse(user.is_treasurer)

    def test_pastor_and_treasurer(self):
        user = CustomUser.objects.create(username="test_user")
        user.type = CustomUser.Types.STAFF
        user.is_pastor = True
        user.is_treasurer = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.STAFF)
        self.assertTrue(user.is_pastor)
        self.assertTrue(user.is_treasurer)
        self.assertFalse(user.is_secretary)

        user.type = CustomUser.Types.REGULAR
        user.save()

        self.assertEqual(user.type, CustomUser.Types.STAFF)
        self.assertTrue(user.is_pastor)
        self.assertTrue(user.is_treasurer)
        self.assertFalse(user.is_secretary)

    def test_pastor_and_treasurer_and_secretary(self):
        user = CustomUser.objects.create(username="test_user")
        user.type = CustomUser.Types.STAFF
        user.is_pastor = True
        user.is_treasurer = True
        user.is_secretary = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.STAFF)
        self.assertTrue(user.is_pastor)
        self.assertTrue(user.is_treasurer)
        self.assertTrue(user.is_secretary)

        user.type = CustomUser.Types.REGULAR
        user.save()

        self.assertEqual(user.type, CustomUser.Types.STAFF)
        self.assertTrue(user.is_pastor)
        self.assertTrue(user.is_treasurer)
        self.assertTrue(user.is_secretary)

    def test_treasurer_and_secretary(self):
        user = CustomUser.objects.create(username="test_user")
        user.type = CustomUser.Types.STAFF
        user.is_pastor = False
        user.is_treasurer = True
        user.is_secretary = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.STAFF)
        self.assertFalse(user.is_pastor)
        self.assertTrue(user.is_treasurer)
        self.assertTrue(user.is_secretary)

        user.type = CustomUser.Types.REGULAR
        user.save()

        self.assertEqual(user.type, CustomUser.Types.STAFF)
        self.assertFalse(user.is_pastor)
        self.assertTrue(user.is_treasurer)
        self.assertTrue(user.is_secretary)

    def test_simpleuser_with_function(self):
        user = CustomUser.objects.create(username="test_user")
        user.is_pastor = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.SIMPLE_USER)
        self.assertFalse(user.is_pastor)

        user.is_secretary = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.SIMPLE_USER)
        self.assertFalse(user.is_secretary)

        user.is_treasurer = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.SIMPLE_USER)
        self.assertFalse(user.is_treasurer)

    def test_congregated_with_function(self):
        user = CustomUser.objects.create(username="test_user")
        user.type = CustomUser.Types.CONGREGATED
        user.is_pastor = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.CONGREGATED)
        self.assertFalse(user.is_pastor)

        user.is_secretary = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.CONGREGATED)
        self.assertFalse(user.is_secretary)

        user.is_treasurer = True
        user.save()

        self.assertEqual(user.type, CustomUser.Types.CONGREGATED)
        self.assertFalse(user.is_treasurer)
