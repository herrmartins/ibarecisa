from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from unittest.mock import MagicMock, patch
from treasury.models import (TransactionModel, MonthlyBalance, CategoryModel)
from users.models import CustomUser
from io import BytesIO
from django.utils import timezone
from PIL import Image
from django.utils.timezone import now
from model_bakery import baker
import shutil
from tempfile import mkdtemp
from django.core.files.storage import Storage
import os
from treasury.tests.test_utils import get_test_image_file


class FakeStorage(Storage):
    def __init__(self, base_location):
        self.base_location = base_location
        self.files = {}

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        normalized_name = os.path.normpath(name)
        self.files[normalized_name] = content
        return normalized_name

    def delete(self, name):
        if name in self.files:
            del self.files[name]

    def exists(self, name):
        normalized_name = os.path.normpath(name)
        return normalized_name in self.files

    def path(self, name):
        normalized_path = os.path.normpath(
            os.path.join(self.base_location, name))
        return normalized_path

    def __del__(self):
        shutil.rmtree(self.base_location)


class TransactionModelMethodsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_media_root = mkdtemp()
        cls.storage = FakeStorage(base_location=cls.temp_media_root)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if hasattr(cls, 'storage') and hasattr(cls.storage, 'base_location'):
            shutil.rmtree(cls.storage.base_location, ignore_errors=True)

    def setUp(self):
        super().setUp()
        TransactionModel.acquittance_doc.field.storage = self.storage
        image_io = BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(image_io, 'JPEG')
        image_io.seek(0)

        self.image = SimpleUploadedFile(
            name='test.jpg', content=image_io.getvalue(), content_type='image/jpeg')

        self.user = CustomUser.objects.create(username='testuser', email='treasury_tx_methods@example.com')

        self.category = CategoryModel.objects.create(name='Test Category')

        current_month = now().date().replace(day=1)
        MonthlyBalance.objects.create(
            month=current_month, is_first_month=True, balance=1000)

    def test_save_new_transaction(self):
        transaction = baker.make(TransactionModel, acquittance_doc=self.image)
        self.assertIsNotNone(transaction.pk)

    def create_transaction(self, **kwargs):
        doc = get_test_image_file()
        defaults = {
            "user": self.user,
            "category": self.category,
            "description": "Test Transaction",
            "amount": 100,
            "date": timezone.now().date(),
            "is_positive": True,
            "acquittance_doc": doc,
        }
        defaults.update(kwargs)
        return baker.make("TransactionModel", **defaults)

    def test_delete_transaction(self):
        transaction = baker.make("TransactionModel", acquittance_doc=get_test_image_file())

        transaction_id = transaction.id
        transaction.delete()

        try:
            still_exists = TransactionModel.objects.get(id=transaction_id)
        except TransactionModel.DoesNotExist:
            still_exists = None

        self.assertIsNone(still_exists, "Transaction should not exist in the database anymore.")

    def test_save_new_transaction_with_future_date(self):
        future_date = timezone.now().date() + timezone.timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.create_transaction(date=future_date)

    def test_update_transaction_changes_file(self):
        new_image = get_test_image_file()
        transaction = baker.make(
            'TransactionModel', acquittance_doc=get_test_image_file())
        old_image_path = transaction.acquittance_doc.path

        transaction.acquittance_doc = new_image
        transaction.save()

        self.assertFalse(transaction.acquittance_doc.storage.exists(
            old_image_path), "Old file should have been deleted but still exists.")

    def test_update_transaction_no_file_change(self):
        transaction = self.create_transaction()
        with patch.object(transaction.acquittance_doc, 'delete', MagicMock(name="delete")) as mock_delete:
            transaction.description = "Updated description"
            transaction.save()
            self.assertFalse(mock_delete.called)

    def test_direct_dictionary_manipulation(self):
        test_key = "test\\path\\file.jpeg"
        test_content = "dummy content"
        self.storage.files[test_key] = test_content
        assert test_key in self.storage.files
        del self.storage.files[test_key]
        assert test_key not in self.storage.files

    def test_storage_delete_directly(self):
        file_name = 'test_delete.jpg'
        content = b'Test content'
        # Use internal method to bypass any Django model behavior
        self.storage._save(file_name, content)

        # Now try deleting directly using the storage
        self.storage.delete(file_name)
        self.assertFalse(file_name in self.storage.files,
                         "The file should have been deleted from storage.")
