from django.test import TestCase
from treasury.models import MonthlyBalance
from users.models import CustomUser
from treasury.models import TransactionModel, TransactionEditHistory
from django.db.models.signals import pre_delete
from treasury.signals import track_transaction_edit
import datetime
from model_bakery import baker


class TransactionSignalTests(TestCase):
    def setUp(self):
        # Setting up a user and a transaction
        self.user = CustomUser.objects.create(username="testuser", password="12345")
        self.first_balance = baker.make(
            "MonthlyBalance", month=datetime.date(2021, 1, 1), is_first_month=True
        )
        self.transaction = TransactionModel.objects.create(
            user=self.user,
            description="Original Description",
            amount=100,
            date=datetime.date(2022, 1, 1),
        )

    def test_track_transaction_edit_on_delete(self):
        pre_delete.connect(track_transaction_edit, sender=TransactionModel)

        self.transaction.delete()

        history = TransactionEditHistory.objects.last()
        self.assertIsNotNone(history)
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.original_description, "Original Description")
        self.assertEqual(history.original_amount, 100)
        self.assertEqual(history.original_date, datetime.date(2022, 1, 1))
        self.assertEqual(history.edited_description, "Original Description")
        self.assertEqual(history.edited_amount, 100)
        self.assertEqual(history.edited_date.date(), datetime.date(2022, 1, 1))

        # Disconnect the signal to clean up
        pre_delete.disconnect(track_transaction_edit, sender=TransactionModel)

    def test_transaction_does_not_exist(self):
        with self.assertLogs("treasury.signals", level="INFO") as log:
            temp_transaction = TransactionModel(
                user=self.user,
                description="Temp Description",
                amount=50,
                date=datetime.date(2022, 1, 1),
            )
            temp_transaction.pk = 999  # Assuming this PK does not exist in the database
            temp_transaction.delete()

            # Check if the expected message is in the logs
            expected_log_message = "Pre_delete chamado, mas não há transaçao..."
            found = any(expected_log_message in message for message in log.output)
            self.assertTrue(found, "Pre_delete chamado, mas não há transaçao...")
