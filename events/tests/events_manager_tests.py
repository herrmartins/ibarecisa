from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from events.models import Event, Venue, EventCategory
from users.models import CustomUser
from model_bakery import baker


class EventManagerTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(username='testuser', email='events_manager_user@example.com')
        self.event_manager = Event.objects
        self.current_date = timezone.now()
        self.venue = baker.make(Venue)
        baker.make(EventCategory, _quantity=3)

        for month in range(1, 13):
            future_date = self.current_date + timedelta(days=30 * month)

            start_date = future_date.replace(year=self.current_date.year)

            end_date = start_date + timedelta(days=3)
            baker.make(Event,
                       user=self.user,
                       title=f"Event {month}",
                       start_date=start_date,
                       end_date=end_date,
                       price=50.00,
                       location_id=1,
                       contact_user_id=1,
                       contact_name="Test Contact",
                       )

        self.yesterday_event = baker.make(Event,
                                          title="Yesterday's Event",
                                          start_date=self.current_date -
                                          timedelta(days=2),
                                          end_date=self.current_date -
                                          timedelta(days=1),
                                          price=50.00,
                                          location_id=1,
                                          contact_user_id=1,
                                          contact_name="Test Contact",
                                          )

    def test_events_by_month_current_year(self):
        events_by_month = self.event_manager.events_by_month_current_year()

        self.assertEqual(len(events_by_month), 12)

        for month_num, events in events_by_month.items():
            month = self.current_date.replace(day=1, month=month_num)
            self.assertTrue(all(event.start_date.month ==
                            month_num for event in events))
            self.assertTrue(all(event.start_date.year ==
                            self.current_date.year for event in events))
            self.assertTrue(
                all(event.start_date >= self.current_date for event in events))
            self.assertNotIn(self.yesterday_event, events)
