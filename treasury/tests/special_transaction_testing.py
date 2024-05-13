from django.test import TestCase
from django.utils import timezone
from treasury.utils import check_and_create_missing_balances
from treasury.models import TransactionModel, MonthlyBalance, CategoryModel
from users.models import CustomUser
from model_mommy import mommy
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from django.db import transaction


class SpecialTransactionModelTests(TestCase):
    def setUp(self):
        self.current_month = timezone.now().date().replace(day=1)
        self.five_months_ago = self.current_month - relativedelta(months=5)
        self.four_months_ago = self.current_month - relativedelta(months=4)
        self.one_month_ago = self.current_month - relativedelta(months=1)
        self.a_year_ago = self.current_month - relativedelta(months=12)
        self.eleven_months_ago = self.current_month - relativedelta(months=11)
        self.cat_1 = mommy.make(CategoryModel, name="Sample Category 1")
        self.cat_2 = mommy.make(CategoryModel, name="Sample Category 2")
        self.user = CustomUser.objects.create_user(
            username="test_user", password="password"
        )

    def test_create_transactions_no_monthly_balance(self):
        mommy.make(
            MonthlyBalance, month=self.a_year_ago, balance=100, is_first_month=True
        )

        MonthlyBalance.objects.get(month=self.five_months_ago).delete(is_testing=True)

        transaction = mommy.make(
            TransactionModel, date=self.five_months_ago, category=self.cat_1
        )

        queried_monthly_balance = None

        try:
            queried_monthly_balance = MonthlyBalance.objects.get(
                month=self.current_month
            )
        except MonthlyBalance.DoesNotExist:
            check_and_create_missing_balances(self.five_months_ago)

        self.assertIsNotNone(
            queried_monthly_balance, "MonthlyBalance for this month should exist"
        )
        number_of_balances = MonthlyBalance.objects.all().count()

        expected_balance_c_month = Decimal(100) + Decimal(transaction.amount)
        self.assertEqual(expected_balance_c_month, queried_monthly_balance.balance)
        # print("ALL MONTHS AFTER ALL", MonthlyBalance.objects.all().order_by("month"))
        self.assertEqual(number_of_balances, 13)

    def test_create_transactions_no_monthly_balances(self):
        mommy.make(
            MonthlyBalance, month=self.a_year_ago, balance=100, is_first_month=True
        )

        MonthlyBalance.objects.get(month=self.five_months_ago).delete(is_testing=True)
        MonthlyBalance.objects.get(month=self.four_months_ago).delete(is_testing=True)
        MonthlyBalance.objects.get(month=self.one_month_ago).delete(is_testing=True)

        with transaction.atomic():
            my_transaction = mommy.make(
                TransactionModel, date=self.five_months_ago, category=self.cat_1
            )

        queried_monthly_balance = None

        try:
            queried_monthly_balance = MonthlyBalance.objects.get(
                month=self.current_month
            )
        except MonthlyBalance.DoesNotExist:
            check_and_create_missing_balances(self.current_month)

        self.assertIsNotNone(
            queried_monthly_balance, "MonthlyBalance for this month should exist"
        )

        number_of_balances = MonthlyBalance.objects.all().count()

        expected_balance_c_month = Decimal(100) + Decimal(my_transaction.amount)
        self.assertEqual(expected_balance_c_month, queried_monthly_balance.balance)
        self.assertEqual(number_of_balances, 13)
