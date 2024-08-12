from django.test import TestCase
from events.models import EventCategory
from django.core.exceptions import ValidationError


class EventCategoryModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test data that will be used in the tests
        EventCategory.objects.create(
            name='Test Category', description='This is a test category')

    # def test_event_category_creation(self):
    #     category = EventCategory.objects.get(id=1)
    #     self.assertEqual(category.name, 'Test Category')
    #     self.assertEqual(category.description, 'This is a test category')

    # def test_event_category_str_method(self):
    #     category = EventCategory.objects.get(id=1)
    #     self.assertEqual(str(category), 'Test Category')

    # def test_unique_name_constraint(self):
    #     # Attempt to create a category with the same name as the existing one
    #     with self.assertRaises(Exception):
    #         EventCategory.objects.create(
    #             name='Test Category', description='Duplicate name')

    # def test_blank_name_field(self):
    #     # Attempt to create a category with a blank name (should raise ValidationError)
    #     with self.assertRaises(ValidationError):
    #         EventCategory.objects.create(name='', description='Invalid Category')

    # def test_null_description_field(self):
    #     # Create a category with a null description
    #     category = EventCategory.objects.create(
    #         name='Third Category', description=None)
    #     self.assertIsNone(category.description)

    # def test_blank_name_field(self):
    #     # Attempt to create a category with a blank name (should raise ValidationError)
    #     with self.assertRaises(Exception):
    #         EventCategory.objects.create(
    #             name='', description='Invalid Category')

    # def test_null_name_field(self):
    #     # Attempt to create a category with a null name (should raise ValidationError)
    #     with self.assertRaises(Exception):
    #         EventCategory.objects.create(
    #             name=None, description='Invalid Category')
