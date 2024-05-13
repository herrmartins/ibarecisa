from rest_framework.test import APITestCase
from django.urls import reverse
from treasury.models import TransactionModel, CategoryModel
from secretarial.models import MinuteExcerptsModel
from users.models import CustomUser
from decimal import Decimal
from model_bakery import baker
from datetime import date
from django.test import override_settings
from rest_framework import status
from treasury.tests.test_utils import get_test_image_file


@override_settings(DEFAULT_FILE_STORAGE='treasury.tests.fake_storage.InMemoryStorage')
class TestViews(APITestCase):
    def setUp(self):
        self.balance_date = date(2022, 12, 1)
        self.date = date(2023, 6, 1)
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.category = baker.make("treasury.CategoryModel")
        baker.make("treasury.MonthlyBalance",
                   month=self.balance_date, is_first_month=True)
        baker.make("CustomUser", first_name="Mary",
                   type=CustomUser.Types.REGULAR)
        baker.make("secretarial.MinuteTemplateModel", body="Lorem ipsum...")
        baker.make("secretarial.MeetingMinuteModel", body="Lorem ipsum...")
        self.transaction = baker.make("TransactionModel")

    def test_file_upload(self):
        url = reverse("post-transaction")
        category = baker.make(CategoryModel)
        # Recreate the test image file just before the request
        test_image = get_test_image_file()
        data = {
            "user": self.user.id,
            "category": category.id,
            "description": "Test Transaction2",
            "amount": "200.00",
            "is_positive": True,
            "date": self.date,
            "acquittance_doc": test_image,
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_current_balance(self):
        TransactionModel.objects.create(
            user=self.user,
            description="Test Transaction",
            amount=Decimal(str(500.00)),
            date=self.date,
        )

        url = reverse("get-current-balance")
        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("current_balance", response.data)
        self.assertIn("last_month_balance", response.data)

    def test_transaction_cat_list(self):
        url = reverse("get-transactions")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_create_transaction(self):
        url = reverse("post-transaction")
        category = baker.make(CategoryModel)
        data = {
            "user": 1,  # Replace with the appropriate user ID
            "category": category.id,  # Replace with the category ID if needed
            "description": "Test Transaction2",
            "amount": "200.00",
            "is_positive": True,
            "date": self.date,
            "acquittance_doc": get_test_image_file(),
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_transaction_invalid_data(self):
        url = reverse("post-transaction")
        data = {
            # Invalid data here
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_transaction(self):
        url = reverse("delete-transaction", kwargs={"pk": self.transaction.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TransactionModel.objects.filter(
            pk=self.transaction.pk).exists())

    def test_get_data(self):
        MinuteExcerptsModel.objects.create()

        url = reverse("get-data")
        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_detailed_data(self):
        minute_excerpt = baker.make(MinuteExcerptsModel)
        pk = 1 
        url = reverse("get-detailed-data", kwargs={"pk": pk})
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unified_search(self):
        url = reverse("secretarial-search")
        user_data = {"category": "users", "searched": "John Doe"}
        response = self.client.post(url, user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        member_data = {"category": "members", "searched": "Rafael"}
        response = self.client.post(url, member_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        min_template_data = {"category": "templates", "searched": "Lorem"}
        response = self.client.post(url, min_template_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        minute_data = {"category": "minutes", "searched": "Lorem"}
        response = self.client.post(url, minute_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invalid_data = {"category": "invalid", "searched": "Lorem"}
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
