from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser
from django.contrib.auth.models import Group, Permission
from treasury.models import MonthlyBalance, TransactionModel, CategoryModel
from model_bakery import baker
from datetime import date, datetime
import unittest
from treasury.utils import (
    get_aggregate_transactions_by_category,
    get_total_transactions_amount,
)
from dateutil.relativedelta import relativedelta


class GenerateMonthlyReportViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.date = date(2023, 11, 1)
        cls.date_before = date(2023, 10, 1)
        cls.current_date = datetime.now()
        cls.current_month = cls.current_date.month
        cls.current_year = cls.current_date.year

        cls.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        cls.treasury_group = Group.objects.create(name="treasury")
        cls.permission = Permission.objects.get(codename="view_monthlyreportmodel")
        cls.treasury_group.permissions.add(cls.permission)
        cls.user.groups.add(cls.treasury_group)
        cls.user.user_permissions.add(cls.permission)
        cls.cat_1 = baker.make(CategoryModel, name="Sample Cat. 1")
        cls.cat_2 = baker.make(CategoryModel, name="Sample Cat. 2")
        baker.make(MonthlyBalance, month=cls.date_before, balance=100, is_first_month=True)
        baker.make(TransactionModel, date=cls.date, amount=10, category=cls.cat_1)
        baker.make(TransactionModel, date=cls.date, amount=15, category=cls.cat_1)
        baker.make(TransactionModel, date=cls.date, amount=70, category=cls.cat_2)
        baker.make(TransactionModel, date=cls.date, amount=100, category=cls.cat_1)
        baker.make(TransactionModel, date=cls.date, amount=-50, category=cls.cat_2)
        baker.make(TransactionModel, date=cls.date, amount=-25, category=cls.cat_1)

    def setUp(self):
        self.client = Client()
        self.generate_report_url = reverse(
            "treasury:gen-report", kwargs={"month": 11, "year": 2023}
        )
        self.login_url = reverse("login")

    def test_unauthorized_access(self):
        response = self.client.get(self.generate_report_url)
        self.assertEqual(response.status_code, 302)

    def test_authorized_access(self):
        self.client.force_login(self.user)
        response = self.client.get(self.generate_report_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "treasury/monthly_report_generator.html")

    def test_existing_monthly_balance(self):
        self.client.force_login(self.user)
        response = self.client.get(self.generate_report_url)
        self.assertEqual(response.status_code, 200)
        balance = response.context["total_balance"]
        expected_balance = 220

        self.assertEqual(balance, expected_balance)

    def test_non_existing_monthly_balance(self):
        self.client.force_login(self.user)
        url = reverse("treasury:gen-report", kwargs={"month": 7, "year": 2023})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_current_month_blocking(self):
        current_date = date.today()
        url = reverse(
            "treasury:gen-report",
            kwargs={"month": current_date.month, "year": current_date.year},
        )
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_no_transaction_data(self):
        self.client.force_login(self.user)
        url = reverse("treasury:gen-report", kwargs={"month": 5, "year": 2022})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_amount_of_transactions(self):
        self.client.force_login(self.user)
        response = self.client.get(self.generate_report_url)
        positive_transactons = response.context["total_ptransactions"]
        negative_transactions = response.context["total_ntransactions"]

        expected_positive_transactions = 195
        expected_negative_transactions = -75

        self.assertEqual(response.status_code, 200)

        self.assertEqual(positive_transactons, expected_positive_transactions)
        self.assertEqual(negative_transactions, expected_negative_transactions)

    def test_monthly_balance_calculation(self):
        TransactionModel.objects.all().delete()
        MonthlyBalance.objects.all().delete()
        main_date = date.today().replace(day=1) - relativedelta(months=2)

        previous_month = main_date - relativedelta(months=1)

        next_month = main_date + relativedelta(months=1)

        baker.make(MonthlyBalance, month=previous_month, balance=100, is_first_month=True)

        baker.make(TransactionModel, date=main_date, amount=50)
        baker.make(TransactionModel, date=main_date, amount=30)

        self.client.force_login(self.user)

        generate_report_url = reverse(
            "treasury:gen-report",
            kwargs={"month": main_date.month, "year": main_date.year},
        )

        response = self.client.get(generate_report_url)
        self.assertEqual(response.status_code, 200)

        pm_balance = response.context["pm_balance"]
        total_balance = response.context["total_balance"]

        expected_pm_balance = 100
        expected_total_balance = 180

        self.assertEqual(pm_balance, expected_pm_balance)
        self.assertEqual(total_balance, expected_total_balance)

        baker.make(TransactionModel, date=main_date, amount=-20)

        response = self.client.get(generate_report_url)
        self.assertEqual(response.status_code, 200)

        pm_balance = response.context["pm_balance"]
        total_balance = response.context["total_balance"]

        expected_total_balance = 160
        self.assertEqual(total_balance, expected_total_balance)

        baker.make(TransactionModel, date=next_month, amount=-30)
        baker.make(TransactionModel, date=next_month, amount=70)

        generate_report_url = reverse(
            "treasury:gen-report",
            kwargs={"month": next_month.month, "year": next_month.year},
        )

        response = self.client.get(generate_report_url)
        self.assertEqual(response.status_code, 200)

        pm_balance = response.context["pm_balance"]
        total_balance = response.context["total_balance"]

        expected_pm_balance = 160
        expected_total_balance = 200

        self.assertEqual(pm_balance, expected_pm_balance)
        self.assertEqual(total_balance, expected_total_balance)


if __name__ == "__main__":
    unittest.main()
