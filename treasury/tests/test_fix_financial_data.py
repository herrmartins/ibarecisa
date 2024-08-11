from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Permission
from users.models import CustomUser
from django.urls import reverse
from treasury.models import MonthlyBalance, TransactionModel
from treasury.views import FixFinancialDataView
from django.contrib.messages.storage.fallback import FallbackStorage
from model_bakery import baker
from datetime import date
from django.core.exceptions import PermissionDenied


class FixFinancialDataViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username="testuser", password="12345"
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="add_transactionmodel")
        )
        self.view = FixFinancialDataView.as_view()

        # Create the first month balance
        self.first_month_balance = MonthlyBalance.objects.create(
            month=date(2024, 1, 1), balance=1000, is_first_month=True
        )

        # Fetch or create subsequent months
        self.second_month_balance, _ = MonthlyBalance.objects.get_or_create(
            month=date(2024, 2, 1), defaults={"balance": 0}
        )
        self.third_month_balance, _ = MonthlyBalance.objects.get_or_create(
            month=date(2024, 3, 1), defaults={"balance": 0}
        )
        baker.make(TransactionModel, date=date(2024, 2, 15), amount=500)
        baker.make(TransactionModel, date=date(2024, 3, 10), amount=300)

    def test_fix_financial_data_success(self):
        request = self.factory.post(reverse("treasury:fix-financial-data"))
        request.user = self.user
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        response = self.view(request)

        self.first_month_balance.refresh_from_db()
        self.second_month_balance.refresh_from_db()
        self.third_month_balance.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"], reverse("treasury:check-treasury-health")
        )
        self.assertEqual(self.second_month_balance.balance, 1500)
        self.assertEqual(self.third_month_balance.balance, 1800)

    def test_fix_financial_data_error(self):
        MonthlyBalance.objects.all().delete()  # Delete all MonthlyBalance to induce an error

        request = self.factory.post(reverse("treasury:fix-financial-data"))
        request.user = self.user
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        response = self.view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"], reverse("treasury:check-treasury-health")
        )
        self.assertTrue(
            any(
                message.message
                == "An error occurred while fixing financial data: MonthlyBalance matching query does not exist."
                for message in messages
            )
        )

    def test_permission_denied(self):
        unauthorized_user = CustomUser.objects.create_user(
            username="unauthorized", password="12345"
        )
        request = self.factory.post(reverse("treasury:fix-financial-data"))
        request.user = unauthorized_user

        with self.assertRaises(PermissionDenied):
            self.view(request)
