from django.test import TestCase
from treasury.models import (
    MonthlyReportModel,
    MonthlyTransactionByCategoryModel,
    MonthlyBalance,
    TransactionModel,
    CategoryModel,
)
from django.db.models.signals import post_save
from treasury.signals import post_save_monthly_report
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from model_mommy import mommy
from treasury.utils import get_aggregate_transactions_by_category


class TestMonthlyReportSignal(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.current_month = timezone.now().date().replace(day=1)
        cls.four_months_ago = cls.current_month - relativedelta(months=4)
        cls.three_months_ago = cls.current_month - relativedelta(months=3)
        cls.balance = MonthlyBalance.objects.create(
            month=cls.four_months_ago, is_first_month=True, balance=1000
        )
        post_save.disconnect(post_save_monthly_report, sender=MonthlyReportModel)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        post_save.connect(post_save_monthly_report, sender=MonthlyReportModel)

    def test_monthly_report_signal(self):
        report_date = self.three_months_ago
        category_1 = mommy.make(CategoryModel, name="Tithe")
        category_2 = mommy.make(CategoryModel, name="Offering")
        category_3 = mommy.make(CategoryModel, name="Expense")
        mommy.make(
            TransactionModel,
            _quantity=5,
            amount=10,
            category=category_1,
            date=self.three_months_ago,
        )
        mommy.make(
            TransactionModel,
            _quantity=5,
            amount=10,
            category=category_2,
            date=self.three_months_ago,
        )
        mommy.make(
            TransactionModel,
            _quantity=3,
            amount=-5,
            category=category_3,
            date=self.three_months_ago,
        )

        positive_transactions = get_aggregate_transactions_by_category(
            year=report_date.year, month=report_date.month
        )
        negative_transactions = get_aggregate_transactions_by_category(
            year=report_date.year, month=report_date.month, is_positive=False
        )

        mommy.make(
            MonthlyReportModel,
            month=report_date,
            previous_month_balance=1000.0,
            total_positive_transactions=0,
            total_negative_transactions=0,
            in_cash=0,
            in_current_account=0,
            in_savings_account=0,
            monthly_result=1000,
            total_balance=2000,
        )

        self.assertIn("Tithe", positive_transactions)
        self.assertIn("Offering", positive_transactions)
        self.assertIn("Expense", negative_transactions)
