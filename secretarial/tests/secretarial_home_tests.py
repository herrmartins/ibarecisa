from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser
from secretarial.views import SecretarialHomeView
from django.contrib.auth.models import Permission
from model_mommy import mommy


class SecretarialHomeViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.regular_user = CustomUser.objects.create(
            username="regular_user", type=CustomUser.Types.REGULAR
        )
        cls.staff_user = CustomUser.objects.create(
            username="staff_user", type=CustomUser.Types.STAFF
        )
        cls.visitor_user = CustomUser.objects.create(
            username="visitor_user", type=CustomUser.Types.CONGREGATED
        )

    def test_view_redirects_for_unauthenticated_users(self):
        response = self.client.get(reverse("secretarial:home"))
        self.assertEqual(response.status_code, 302)

    def test_unauthorized_user_access(self):
        # Create a user without the necessary permission
        unauthorized_user = CustomUser.objects.create_user(
            username="unauthorized", password="testpass"
        )
        self.client.force_login(unauthorized_user)

        # Attempt to access the 'secretarial:home' page
        response = self.client.get(reverse("secretarial:home"))

        # Expecting a status code 403 (forbidden) for unauthorized access
        self.assertEqual(response.status_code, 403)

    def test_view_uses_correct_template(self):
        # Assign the required permission to the regular_user
        permission = Permission.objects.get(codename="view_meetingminutemodel")
        self.regular_user.user_permissions.add(permission)

        self.client.force_login(self.regular_user)
        response = self.client.get(reverse("secretarial:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "secretarial/home.html")

    def test_context_data_for_authorized_user(self):
        # Assign the required permission to the regular_user
        permission = Permission.objects.get(codename="view_meetingminutemodel")
        self.regular_user.user_permissions.add(permission)
        mommy.make(CustomUser, type=CustomUser.Types.REGULAR, _quantity=13)
        mommy.make(CustomUser, type=CustomUser.Types.CONGREGATED, _quantity=15)

        self.client.force_login(self.regular_user)

        response = self.client.get(reverse("secretarial:home"))

        self.assertEqual(response.status_code, 200)

        number_of_members = response.context["number_of_members"]
        number_of_visitors = response.context["number_of_visitors"]

        self.assertIn("number_of_members", response.context)
        self.assertIn("number_of_visitors", response.context)
        # There are more congregated and regulars in the beginning of the code
        self.assertEqual(number_of_members, 15)
        self.assertEqual(number_of_visitors, 16)
