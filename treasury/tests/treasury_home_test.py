from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from treasury.models import MonthlyBalance
from users.models import CustomUser
from datetime import date
from model_mommy import mommy
from unittest.mock import patch
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class TreasuryHomeViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.date = date(2023, 11, 1)
        cls.date_before = date(2023, 10, 1)
        cls.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        cls.treasury_group = Group.objects.create(name="treasury")
        cls.permission = Permission.objects.get(codename="view_transactionmodel")
        cls.treasury_group.permissions.add(cls.permission)
        cls.user.groups.add(cls.treasury_group)
        cls.user.user_permissions.add(cls.permission)

        cls.treasury_home_url = reverse("treasury:home")

    def test_unauthorized_access(self):
        response = self.client.get(self.treasury_home_url)
        self.assertEqual(response.status_code, 302)

    def test_insufficient_permission(self):
        user_without_permission = CustomUser.objects.create_user(
            username="testuser2", email="test2@example.com", password="password123"
        )
        self.client.force_login(user_without_permission)
        response = self.client.get(self.treasury_home_url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.client.force_login(self.user)
        response = self.client.get(self.treasury_home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "treasury/home.html")

    def test_context_data_no_balance(self):
        self.client.force_login(self.user)
        response = self.client.get(self.treasury_home_url)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("previous_month_account_balance", response.context)
        self.assertIn("form_balance", response.context)

    def test_context_data_with_balance(self):
        mommy.make(
            MonthlyBalance, month=self.date_before, is_first_month=True, balance=1000
        )

        self.client.force_login(self.user)
        response = self.client.get(self.treasury_home_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("previous_month_account_balance", response.context)
        self.assertIn("form_transaction", response.context)

    def test_open_treasury_home_without_last_balance(self):
        # Setup date for the test, ensuring no ambiguity in month calculation
        now = timezone.now().replace(day=1).date()
        test_date = now + relativedelta(months=1)
        a_year_ago = now - relativedelta(months=12)

        MonthlyBalance.objects.create(month=a_year_ago, is_first_month=True, balance=10)

        # Patch timezone.now() to return the first day of the next month
        with patch("django.utils.timezone.now", return_value=test_date):
            self.client.force_login(self.user)
            response = self.client.get(self.treasury_home_url)
            self.assertEqual(response.status_code, 200)

    def test_open_treasury_home_without_last_two_or_more_balances(self):
        now = timezone.now().replace(day=1).date()
        test_date = now + relativedelta(months=2)
        a_year_ago = now - relativedelta(months=12)

        MonthlyBalance.objects.create(month=a_year_ago, is_first_month=True, balance=10)

        with patch("django.utils.timezone.now", return_value=test_date):
            self.client.force_login(self.user)
            response = self.client.get(self.treasury_home_url)
            self.assertEqual(response.status_code, 302)
            balances = MonthlyBalance.objects.all().count()
            self.assertEqual(response["Location"], self.treasury_home_url)

        test_date = now + relativedelta(months=7)

        with patch("django.utils.timezone.now", return_value=test_date):
            self.client.force_login(self.user)
            response = self.client.get(self.treasury_home_url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], self.treasury_home_url)
