from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from events.models import Event, Venue, EventCategory
from users.models import CustomUser
from model_bakery import baker


class EventManagerTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(username="testuser")
        self.event_manager = Event.objects
        self.current_date = timezone.now()
        self.venue = baker.make(Venue)
        baker.make(EventCategory, _quantity=3)

        # Create events explicitly for different months
        self.event_january = baker.make(
            Event,
            user=self.user,
            title="January Event",
            start_date=self.current_date.replace(month=1, day=10),
            end_date=self.current_date.replace(month=1, day=13),
            price=50.00,
            location=self.venue,
            contact_user=self.user,
            contact_name="Test Contact",
        )

        self.event_february = baker.make(
            Event,
            user=self.user,
            title="February Event",
            start_date=self.current_date.replace(month=2, day=15),
            end_date=self.current_date.replace(month=2, day=18),
            price=50.00,
            location=self.venue,
            contact_user=self.user,
            contact_name="Test Contact",
        )

        self.event_march = baker.make(
            Event,
            user=self.user,
            title="March Event",
            start_date=self.current_date.replace(month=3, day=5),
            end_date=self.current_date.replace(month=3, day=8),
            price=50.00,
            location=self.venue,
            contact_user=self.user,
            contact_name="Test Contact",
        )

        # Create two events in the same month
        self.event_april_1 = baker.make(
            Event,
            user=self.user,
            title="April Event 1",
            start_date=self.current_date.replace(month=4, day=1),
            end_date=self.current_date.replace(month=4, day=4),
            price=50.00,
            location=self.venue,
            contact_user=self.user,
            contact_name="Test Contact",
        )

        self.event_april_2 = baker.make(
            Event,
            user=self.user,
            title="April Event 2",
            start_date=self.current_date.replace(month=4, day=15),
            end_date=self.current_date.replace(month=4, day=18),
            price=50.00,
            location=self.venue,
            contact_user=self.user,
            contact_name="Test Contact",
        )

        # Create an event in the past
        self.yesterday_event = baker.make(
            Event,
            title="Yesterday's Event",
            start_date=self.current_date - timedelta(days=2),
            end_date=self.current_date - timedelta(days=1),
            price=50.00,
            location=self.venue,
            contact_user=self.user,
            contact_name="Test Contact",
        )

    def test_events_by_month_current_year(self):
        events_by_month = self.event_manager.events_by_month_current_year()

        self.assertEqual(len(events_by_month), 12)

        for month_num, events in events_by_month.items():
            # Check if events are grouped by month correctly
            self.assertTrue(
                all(event.start_date.month == month_num for event in events),
                f"Event found in wrong month: {events}",
            )
            self.assertTrue(
                all(event.start_date.year == self.current_date.year for event in events)
            )
            self.assertTrue(
                all(event.start_date >= self.current_date for event in events)
            )
            self.assertNotIn(self.yesterday_event, events)
