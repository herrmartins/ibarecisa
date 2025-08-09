from django.test import TestCase
from django.utils import timezone
from treasury.models import TransactionModel, MonthlyBalance, CategoryModel
from users.models import CustomUser
from model_bakery import baker
import unittest
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from datetime import date, timedelta
from random import randint
from django.db import models, transaction
import random
from treasury.exceptions import NoInitialMonthlyBalance
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist


class TransactionModelTests(TestCase):
    def setUp(self):
        self.current_month = timezone.now().date().replace(day=1)
        self.two_months_ago = self.current_month - relativedelta(months=2)
        self.two_years_ago = self.current_month - relativedelta(years=2)
        self.a_year_ago = self.current_month - relativedelta(months=12)
        self.five_months_ago = self.current_month - relativedelta(months=5)
        self.four_months_ago = self.current_month - relativedelta(months=4)
        self.eleven_months_ago = self.current_month - relativedelta(months=11)
        self.next_month = self.current_month + relativedelta(months=1)
        self.category_1 = baker.make(CategoryModel, name="Tithe1")
        self.category_2 = baker.make(CategoryModel, name="Offering1")
        self.category_3 = baker.make(CategoryModel, name="Expense1")

        self.user = CustomUser.objects.create_user(
            username="test_user", password="password"
        )
        self.balance = MonthlyBalance.objects.create(
            month=self.a_year_ago, is_first_month=True, balance=100
        )

    def test_create_monthly_balances(self):
        MonthlyBalance.objects.get(
            month=self.five_months_ago).delete(is_testing=True)

        transaction = baker.make(
            TransactionModel, date=self.five_months_ago, category=self.category_1)

        balance = MonthlyBalance.objects.get(month=self.five_months_ago)

        self.assertIsNotNone(balance)

    def test_transaction_without_initial_balance(self):
        MonthlyBalance.objects.all().delete()

        with self.assertRaises(ValidationError):
            transaction = baker.make(
                TransactionModel, date=self.two_years_ago, category=self.category_1)

    def test_add_transaction_future_date(self):
        with self.assertRaises(ValidationError):
            transaction = baker.make(
                TransactionModel, date=self.next_month, category=self.category_1)

    def test_transactions_date_before_first_month(self):
        first_month_balance_before = MonthlyBalance.objects.get(
            is_first_month=True).balance
        transaction = baker.make(
            TransactionModel, date=self.two_years_ago, category=self.category_1)
        first_month_balance_after = MonthlyBalance.objects.get(
            is_first_month=True).balance

        self.assertEqual(first_month_balance_before, first_month_balance_after)

    def test_delete_transaction_before_first_month(self):
        first_month_balance_before = MonthlyBalance.objects.get(
            is_first_month=True).balance
        transaction = baker.make(
            TransactionModel, date=self.two_years_ago, category=self.category_1, amount=11.11)
        first_month_balance_after = MonthlyBalance.objects.get(
            is_first_month=True).balance

        self.assertEqual(first_month_balance_before, first_month_balance_after)

        TransactionModel.objects.get(pk=transaction.pk).delete()
        first_month_balance_before = MonthlyBalance.objects.get(
            is_first_month=True).balance
        first_month_balance_after = MonthlyBalance.objects.get(
            is_first_month=True).balance

        self.assertEqual(first_month_balance_before, first_month_balance_after)

    def test_update_balances_on_create_transactions(self):
        MonthlyBalance.objects.all().delete()

        balance = MonthlyBalance.objects.create(
            month=self.a_year_ago, is_first_month=True, balance=100
        )

        transaction1 = baker.make(
            TransactionModel,
            date=self.five_months_ago,
            amount=20,
            category=self.category_1,
        )

        transaction2 = baker.make(
            TransactionModel,
            date=self.two_months_ago,
            amount=30,
            category=self.category_2,
        )

        transaction3 = baker.make(
            TransactionModel,
            date=self.four_months_ago,
            amount=-10,
            category=self.category_3,
        )

        five_months_ago_balance = MonthlyBalance.objects.get(
            month=self.five_months_ago
        ).balance
        assert_value = 120
        self.assertEqual(five_months_ago_balance, assert_value)

        current_month_balance = MonthlyBalance.objects.get(
            month=self.current_month
        ).balance
        assert_value = 140
        self.assertEqual(current_month_balance, assert_value)

    def test_edit_transaction(self):
        transaction = baker.make(
            TransactionModel,
            date=self.current_month,
            amount=100,
            description="Original Description",
            category=self.category_1,
        )

        queried_monthly_balance = MonthlyBalance.objects.get(
            month=self.current_month)
        self.assertEqual(queried_monthly_balance.balance, Decimal(200))

        additional_transaction = baker.make(
            TransactionModel,
            date=self.current_month,
            amount=100,
            description="Description",
            category=self.category_2,
        )

        queried_monthly_balance = MonthlyBalance.objects.get(
            month=self.current_month)

        self.assertEqual(queried_monthly_balance.balance, Decimal(300))

        transaction.amount = 150
        transaction.description = "Updated Description"
        transaction.save()

        queried_monthly_balance = MonthlyBalance.objects.get(
            month=self.current_month)
        self.assertEqual(queried_monthly_balance.balance, Decimal(350))

        additional_transaction.amount = 50
        additional_transaction.save()

        queried_monthly_balance = MonthlyBalance.objects.get(
            month=self.current_month)
        self.assertEqual(queried_monthly_balance.balance, Decimal(300))

        updated_transaction = TransactionModel.objects.get(pk=transaction.pk)
        self.assertEqual(updated_transaction.amount, 150)
        self.assertEqual(updated_transaction.description,
                         "Updated Description")

        negative_transaction = baker.make(
            TransactionModel, amount=-5, date=self.current_month, category=self.category_2,
        )
        queried_monthly_balance = MonthlyBalance.objects.get(
            month=self.current_month)
        self.assertEqual(queried_monthly_balance.balance, Decimal(295))

        negative_transaction.amount = 5
        negative_transaction.save()
        queried_monthly_balance = MonthlyBalance.objects.get(
            month=self.current_month)
        self.assertEqual(queried_monthly_balance.balance, Decimal(305))

    def test_edit_transaction_before_first_month(self):
        transaction = baker.make(
            TransactionModel, date=self.two_years_ago, category=self.category_1)

        first_month_balance_before = MonthlyBalance.objects.get(
            is_first_month=True).balance

        transaction.amount = 10
        transaction.save()

        first_month_balance_after = MonthlyBalance.objects.get(
            is_first_month=True).balance

        self.assertEqual(first_month_balance_before, first_month_balance_after)

    def test_different_operations_before_first_month(self):
        transaction_1 = baker.make(
            TransactionModel, date=self.two_years_ago,
            category=self.category_1, amount=10)
        transaction_2 = baker.make(
            TransactionModel, date=self.two_years_ago,
            category=self.category_1, amount=10)

        first_month_balance_before = MonthlyBalance.objects.get(
            is_first_month=True).balance

        transaction_1.amount = 5
        transaction_1.save()
        # Just to make sure we see changes in the transactions
        self.assertEqual(transaction_1.amount, 5)

        first_month_balance_after = MonthlyBalance.objects.get(
            is_first_month=True).balance

        self.assertEqual(first_month_balance_before, first_month_balance_after)

        transaction_2.delete()
        with self.assertRaises(ObjectDoesNotExist):
            TransactionModel.objects.get(pk=transaction_2.pk)

        first_month_balance_after = MonthlyBalance.objects.get(
            is_first_month=True).balance

        self.assertEqual(first_month_balance_before, first_month_balance_after)

        transaction_3 = baker.make(
            TransactionModel, date=self.two_years_ago,
            category=self.category_1, amount=10)

        first_month_balance_after = MonthlyBalance.objects.get(
            is_first_month=True).balance

        self.assertEqual(first_month_balance_before, first_month_balance_after)

    def test_delete_transaction(self):
        transactions = []
        n = 0
        for i in range(4):
            transaction_date = self.eleven_months_ago + timedelta(
                days=i * 3 * 30
            )  # Every three months

            transactions.append(
                baker.make(
                    TransactionModel,
                    date=transaction_date,
                    amount=10,
                    category=self.category_2,
                )
            )
            n += 1

        this_month_expected_balance = Decimal(n * 10 + 100)

        this_month_balance = MonthlyBalance.objects.get(
            month=self.current_month
        ).balance

        self.assertEqual(this_month_expected_balance, this_month_balance)

        while TransactionModel.objects.exists():
            # Delete the first transaction
            TransactionModel.objects.first().delete()
            n = TransactionModel.objects.count()
            this_month_expected_balance = Decimal(n * 10 + 100)

            this_month_balance = MonthlyBalance.objects.get(
                month=self.current_month
            ).balance
            self.assertEqual(this_month_expected_balance, this_month_balance)

    def test_with_transactions_in_different_months(self):
        current_date = date.today()

        expected_months = [
            self.a_year_ago.replace(day=1) + relativedelta(months=i)
            for i in range(
                (current_date.year - self.a_year_ago.year) * 12
                + current_date.month
                - self.a_year_ago.month
                + 1
            )
        ]

        for i in range(7):
            random_date = expected_months[i]
            amount = randint(-100, 100)
            if not MonthlyBalance.objects.get(month=random_date).is_first_month:
                baker.make(
                    TransactionModel,
                    date=random_date,
                    amount=amount,
                    category=self.category_2,
                )

        all_monthly_balances = MonthlyBalance.objects.filter(
            month__range=(self.a_year_ago, current_date)
        ).order_by("month")

        self.assertEqual(all_monthly_balances.count(), len(expected_months))

        previous_balance = 100

        for balance in all_monthly_balances:
            transactions = TransactionModel.objects.filter(
                date__year=balance.month.year, date__month=balance.month.month
            )

            total_amount = transactions.aggregate(total_amount=models.Sum("amount"))[
                "total_amount"
            ]
            if balance.is_first_month:
                self.assertEqual(balance.balance, previous_balance)
            else:
                if total_amount is not None:
                    expected_balance = previous_balance + total_amount
                    self.assertEqual(balance.balance, expected_balance)
                else:
                    self.assertEqual(balance.balance, previous_balance)

            previous_balance = balance.balance

        all_transactions = []
        for expected_month in expected_months:
            transactions = TransactionModel.objects.filter(
                date__year=expected_month.year, date__month=expected_month.month
            )
            all_transactions.extend(list(transactions))

        transactions_to_update = random.sample(all_transactions, 3)

        for transaction in transactions_to_update:
            new_amount = random.randint(-100, 100)
            transaction.amount = new_amount
            transaction.save()

        updated_monthly_balances = MonthlyBalance.objects.filter(
            month__range=(self.a_year_ago, current_date)
        ).order_by("month")

        for balance in updated_monthly_balances:
            if not balance.is_first_month:
                transactions = TransactionModel.objects.filter(
                    date__year=balance.month.year, date__month=balance.month.month
                )
                total_amount = transactions.aggregate(
                    total_amount=models.Sum("amount")
                )["total_amount"]

                if total_amount is not None:
                    try:
                        previous_month = balance.month - \
                            relativedelta(months=1)
                        previous_month_balance = MonthlyBalance.objects.get(
                            month=previous_month
                        ).balance
                    except Exception:
                        raise NoInitialMonthlyBalance(
                            "ERRO, NÃO EXISTE BALANÇO ANTERIOR"
                        )
                    expected_balance = previous_month_balance + total_amount
                    self.assertEqual(balance.balance, expected_balance)
                else:
                    self.assertEqual(balance.balance, previous_balance)
                previous_balance = balance.balance

    def test_transactions_deletion_affects_monthly_balances(self):
        current_date = date.today()
        MonthlyBalance.objects.all().delete()
        TransactionModel.objects.all().delete()

        baker.make(
            MonthlyBalance, month=self.a_year_ago, balance=100, is_first_month=True
        )

        # Generate a list of expected months between a_year_ago and current_date
        expected_months = [
            self.a_year_ago.replace(day=1) + relativedelta(months=i)
            for i in range(
                (current_date.year - self.a_year_ago.year) * 12
                + current_date.month
                - self.a_year_ago.month
                + 1
            )
        ]

        # Fetch all MonthlyBalance instances within the date range
        all_monthly_balances = MonthlyBalance.objects.filter(
            month__range=(self.a_year_ago, current_date)
        ).order_by("month")

        # Asserting that all monthly balances were created
        self.assertEqual(all_monthly_balances.count(), len(expected_months))

        # Create transactions for a few different months with varying positive and negative amounts

        for i in range(7):
            random_date = expected_months[i]
            amount = randint(-100, 100)
            if not MonthlyBalance.objects.get(month=random_date).is_first_month:
                baker.make(
                    TransactionModel,
                    date=random_date,
                    amount=amount,
                    category=self.category_2,
                )

        previous_balance = 100  # Set the initial previous balance for the first month

        for balance in all_monthly_balances:
            transactions = TransactionModel.objects.filter(
                date__year=balance.month.year, date__month=balance.month.month
            )

            total_amount = transactions.aggregate(total_amount=models.Sum("amount"))[
                "total_amount"
            ]
            if balance.is_first_month:
                self.assertEqual(balance.balance, previous_balance)
            else:
                if total_amount is not None:
                    expected_balance = previous_balance + total_amount
                    self.assertEqual(balance.balance, expected_balance)
                else:
                    self.assertEqual(balance.balance, previous_balance)

            previous_balance = balance.balance

        initial_monthly_balances = MonthlyBalance.objects.all()

        transactions_to_delete = random.sample(
            list(TransactionModel.objects.all()), 3)

        for transaction in transactions_to_delete:
            transaction.delete()

        updated_monthly_balances = MonthlyBalance.objects.filter(
            month__range=(self.a_year_ago, current_date)
        ).order_by("month")

        for initial_balance, updated_balance in zip(
            initial_monthly_balances, updated_monthly_balances
        ):
            if initial_balance.is_first_month:
                self.assertEqual(initial_balance.balance,
                                 updated_balance.balance)
            else:
                initial_total_amount = TransactionModel.objects.filter(
                    date__year=initial_balance.month.year,
                    date__month=initial_balance.month.month,
                ).aggregate(total_amount=models.Sum("amount"))["total_amount"]

                updated_total_amount = TransactionModel.objects.filter(
                    date__year=updated_balance.month.year,
                    date__month=updated_balance.month.month,
                ).aggregate(total_amount=models.Sum("amount"))["total_amount"]

                if (
                    initial_total_amount is not None
                    and updated_total_amount is not None
                ):
                    expected_balance = (
                        initial_balance.balance
                        + initial_total_amount
                        - updated_total_amount
                    )
                    self.assertEqual(updated_balance.balance, expected_balance)
                else:
                    self.assertEqual(updated_balance.balance,
                                     initial_balance.balance)


if __name__ == "__main__":
    unittest.main()
