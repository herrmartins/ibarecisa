from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser
from treasury.models import MonthlyBalance
from django.test.client import Client
from datetime import datetime, date
from django.contrib.auth.models import Group, Permission
from treasury.models import TransactionModel
from model_bakery import baker
from dateutil.relativedelta import relativedelta
from datetime import datetime
from django.utils import timezone


class FinanceReportsListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username="testuser", email="treasury_reports@example.com", password="password123"
        )
        cls.treasury_group = Group.objects.create(name="treasury")
        cls.permission = Permission.objects.get(
            codename="view_transactionmodel")
        cls.treasury_group.permissions.add(cls.permission)
        cls.user.groups.add(cls.treasury_group)

    def setUp(self):
        self.current_month = timezone.now().date().replace(day=1)
        self.two_months_ago = self.current_month - relativedelta(months=2)
        self.a_year_ago = self.current_month - relativedelta(months=12)
        self.five_months_ago = self.current_month - relativedelta(months=5)
        self.four_months_ago = self.current_month - relativedelta(months=4)

        self.client = Client()
        self.user.user_permissions.add(self.permission)
        self.client.login(username="testuser", password="password123")
        self.monthly_balance = baker.make(
            MonthlyBalance,
            month=self.a_year_ago,
            balance=1000.00, is_first_month=True
        )

    def test_user_has_required_permission(self):
        response = self.client.get(reverse("treasury:list-financial-reports"))
        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            self.user.has_perm("treasury.view_transactionmodel"),
            msg="User doesn't have the required permission.",
        )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/treasury/reports")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("treasury:list-financial-reports"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("treasury:list-financial-reports"))
        self.assertTemplateUsed(response, "treasury/reports_list.html")

    def test_view_context_contains_reports(self):
        response = self.client.get(reverse("treasury:list-financial-reports"))
        reports_context = response.context.get("reports")

        self.assertIsNotNone(reports_context, msg="Reports context is None")

        self.assertTrue(
            all(isinstance(report, MonthlyBalance)
                for report in reports_context),
            msg="Reports context contains non-MonthlyBalance objects",
        )

        self.assertGreaterEqual(
            len(reports_context),
            1,
            msg="Reports context does not contain any MonthlyBalance instance",
        )
