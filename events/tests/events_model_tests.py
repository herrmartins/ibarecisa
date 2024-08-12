from django.test import TestCase
from datetime import datetime, timedelta

from model_mommy import mommy
from users.models import CustomUser
from events.models import Event, Venue,EventCategory


class EventModelTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(
            username='test_user1', email='test1@example.com')
        self.user1 = CustomUser.objects.create(
            username='test_user2', email='test@example.com')
        self.venue = Venue.objects.create(
            name='Test Venue', address='123 Test St', capacity=200)
        self.venue1 = Venue.objects.create(
            name='Test Venue 1', address='345 Test St', capacity=100)
        self.category = mommy.make(EventCategory)
        self.event = mommy.make(Event,
                                title='Test Event',
                                start_date=datetime.now(),
                                user=self.user1,
                                location=self.venue1,
                                category=self.category
                                )

    def test_field_constraints(self):
        event = Event.objects.get(title='Test Event')
        self.assertIsNotNone(event.title)
        self.assertIsNotNone(event.start_date)

        # Optional fields can be null or blank
        self.assertIsNone(event.description)
        self.assertIsNone(event.end_date)
        self.assertIsNone(event.price)
        self.assertIsNone(event.contact_name)

    def test_foreign_keys(self):
        event = Event.objects.get(title='Test Event')
        self.assertEqual(event.user, self.user1)
        self.assertEqual(event.location, self.venue1)

    def test_default_values(self):
        # Default value for 'user' and 'location' fields should be set properly
        default_event = mommy.make(Event, title='Default Test Event')
        # Assuming default user ID is 1
        self.assertEqual(default_event.user_id, 1)
        # Assuming default location ID is 1
        self.assertEqual(default_event.location_id, 1)

    def test_deletion_behavior(self):
        # Deleting a related 'CustomUser' should set 'user' to default (ID 1)
        self.user1.delete()
        deleted_user_event = Event.objects.get(title='Test Event')
        self.assertEqual(deleted_user_event.user_id, 1)

        self.venue1.delete()
        deleted_venue_event = Event.objects.get(title='Test Event')
        self.assertEqual(deleted_venue_event.location_id, 1)

    def test_event_creation(self):
        # Test creating an event with mandatory fields
        new_event = mommy.make(Event,
                               title='New Event',
                               start_date=datetime.now(),
                               user=self.user,
                               location=self.venue
                               )
        self.assertEqual(new_event.title, 'New Event')

        # Test creating an event with optional fields
        optional_event = mommy.make(Event,
                                    title='Optional Event',
                                    start_date=datetime.now(),
                                    user=self.user,
                                    location=self.venue,
                                    end_date=datetime.now() + timedelta(days=2),
                                    price=30.00,
                                    contact_user=self.user,
                                    contact_name='Optional Contact'
                                    )
        self.assertEqual(optional_event.price, 30.00)
        self.assertEqual(optional_event.contact_name, 'Optional Contact')

    def test_update_behavior(self):
        event = Event.objects.get(title='Test Event')

        # Test updating 'title', 'description', 'start_date' fields individually
        event.title = 'Updated Title'
        event.save()
        self.assertEqual(event.title, 'Updated Title')

        event.description = 'Updated description'
        event.save()
        self.assertEqual(event.description, 'Updated description')

        event.start_date = datetime.now() + timedelta(days=1)
        event.save()
        self.assertEqual(event.start_date.date(),
                         (datetime.now() + timedelta(days=1)).date())
