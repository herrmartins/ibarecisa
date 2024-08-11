from django.test import TestCase
from model_mommy import mommy
from treasury.models import MonthlyBalance, TransactionModel, CategoryModel
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import random


class MonthlyBalanceModelTest(TestCase):
    def setUp(self):
        self.current_month = timezone.now().date().replace(day=1)
        self.two_months_ago = self.current_month - relativedelta(months=2)
        self.one_month_ago = self.current_month - relativedelta(months=1)
        self.five_months_ago = self.current_month - relativedelta(months=5)
        self.four_months_ago = self.current_month - relativedelta(months=4)
        self.a_year_ago = self.current_month - relativedelta(months=12)
        self.balance = MonthlyBalance.objects.create(
            month=self.current_month, is_first_month=True, balance=10
        )
        self.category_1 = mommy.make(CategoryModel, name="One Cat")
        self.category_2 = mommy.make(CategoryModel, name="Two Cat")
        self.category_3 = mommy.make(CategoryModel, name="Expense 2")

    def test_monthly_balance_creation(self):
        self.assertTrue(isinstance(self.balance, MonthlyBalance))
        self.assertEqual(
            self.balance.__str__(),
            f"{self.balance.month} - {self.balance.balance} - {self.balance.is_first_month}",
        )

    def test_unique_month(self):
        with self.assertRaises(Exception):
            duplicate_balance = MonthlyBalance.objects.create(
                month=self.current_month, is_first_month=True, balance=200.0
            )

    def test_delete_balance(self):
        with self.assertRaises(Exception):
            MonthlyBalance.objects.get(month=self.current_month).delete()

    def test_create_transaction_without_any_balances(self):
        MonthlyBalance.objects.all().delete()
        with self.assertRaises(Exception):
            mommy.make(TransactionModel, category=self.category_1)

    def test_monthly_balance_creation_year_ago(self):
        MonthlyBalance.objects.all().delete()
        MonthlyBalance.objects.create(
            month=self.a_year_ago, is_first_month=True, balance=10
        )

        balances = MonthlyBalance.objects.all().order_by("month")

    def test_monthly_balance_reconstruction(self):
        MonthlyBalance.objects.all().delete()
        MonthlyBalance.objects.create(
            month=self.a_year_ago, is_first_month=True, balance=10
        )

        MonthlyBalance.objects.get(month=self.five_months_ago).delete(is_testing=True)
        MonthlyBalance.objects.get(month=self.four_months_ago).delete(is_testing=True)
        MonthlyBalance.objects.get(month=self.one_month_ago).delete(is_testing=True)

        MonthlyBalance.objects.create(
            month=self.five_months_ago, is_first_month=False, balance=10
        )

        balances = MonthlyBalance.objects.all().order_by("month")
        self.assertEqual(balances.count(), 13)

    def test_updating_subsequent_monthly_balances(self):
        MonthlyBalance.objects.all().delete()
        MonthlyBalance.objects.create(
            month=self.a_year_ago, is_first_month=True, balance=10
        )

        balance_to_edit = MonthlyBalance.objects.get(month=self.five_months_ago)
        balance_to_edit.balance += 5
        balance_to_edit.save()

        last_balance = MonthlyBalance.objects.all().last()
        self.assertEqual(last_balance.balance, 15)

        new_balance_to_edit = MonthlyBalance.objects.get(month=self.four_months_ago)
        new_balance_to_edit.balance += 5
        new_balance_to_edit.save()

        last_balance = MonthlyBalance.objects.all().last()
        self.assertEqual(last_balance.balance, 20)

        value = Decimal(random.uniform(10.5, 75.5)).quantize(Decimal("0.01"))
        # value = 10
        other_balance_to_edit = MonthlyBalance.objects.get(month=self.a_year_ago)
        other_balance_to_edit.balance += value
        other_balance_to_edit.save()

        last_balance = MonthlyBalance.objects.get(month=self.current_month)
        value_to_assert = value + 20
        self.assertAlmostEqual(last_balance.balance, value_to_assert, places=2)
