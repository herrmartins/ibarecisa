from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser
from django.contrib.auth.models import Group, Permission
from treasury.models import MonthlyBalance, TransactionModel
from model_mommy import mommy
from datetime import date
from dateutil.relativedelta import relativedelta


class MonthlyCarchiveViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.date = date(2023, 12, 1)
        cls.date_before = date(2023, 11, 1)

        cls.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        cls.treasury_group = Group.objects.create(name="treasury")
        cls.permission = Permission.objects.get(codename="view_transactionmodel")
        cls.treasury_group.permissions.add(cls.permission)
        cls.user.groups.add(cls.treasury_group)
        cls.user.user_permissions.add(cls.permission)

        mommy.make("treasury.MonthlyBalance", month=cls.date_before, is_first_month=True )
        mommy.make("treasury.TransactionModel", date=cls.date, _quantity=10)

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.get(username="testuser")
        self.user.user_permissions.add(self.permission)
        self.client.login(username="testuser", password="password123")

    def test_view_has_permission(self):
        url = reverse(
            "treasury:monthly-transactions",
            kwargs={"year": self.date.year, "month": self.date.month},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_no_permission(self):
        # Remove user's permission for the test
        self.user.user_permissions.remove(self.permission)
        url = reverse(
            "treasury:monthly-transactions",
            kwargs={"year": self.date.year, "month": self.date.month},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_view_template_used(self):
        url = reverse(
            "treasury:monthly-transactions",
            kwargs={"year": self.date.year, "month": self.date.month},
        )
        response = self.client.get(url)
        self.assertTemplateUsed(response, "treasury/detailed_report.html")

    def test_view_context_data(self):
        url = reverse(
            "treasury:monthly-transactions",
            kwargs={"year": self.date.year, "month": self.date.month},
        )
        response = self.client.get(url)
        self.assertIn("finance_entries", response.context)
        self.assertIn("year", response.context)
        self.assertIn("month", response.context)

    def test_view_previous_month_balance(self):
        # Create MonthlyBalance for the previous month
        previous_month = self.date - relativedelta(months=1)

        url = reverse(
            "treasury:monthly-transactions",
            kwargs={"year": self.date.year, "month": self.date.month},
        )
        response = self.client.get(url)

    def test_view_no_previous_month_balance(self):
        # No MonthlyBalance for the previous month
        url = reverse(
            "treasury:monthly-transactions",
            kwargs={"year": self.date.year, "month": self.date.month},
        )
        response = self.client.get(url)

    def test_quantity_of_transactions(self):
        expected_transactions_count = 10
        transactions_count = TransactionModel.objects.all().count()
        self.assertEqual(transactions_count, expected_transactions_count)

    def test_exist_monthly_balance_transactions(self):
        monthly_balance = MonthlyBalance.objects.get(month=self.date)
        self.assertIsNotNone(monthly_balance)
