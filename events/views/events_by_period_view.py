from django.http import JsonResponse
from django.views import View
from django.utils.dateparse import parse_date
from events.models import Event
from django.shortcuts import reverse


class EventsByPeriodView(View):
    def get(self, request, *args, **kwargs):
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if not start_date or not end_date:
            return JsonResponse(
                {"error": "A data de início e do fim são obrigatórias."}, status=400
            )

        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        if not start_date or not end_date:
            return JsonResponse({"error": "Formato inválido."}, status=400)

        events = Event.objects.filter(
            start_date__gte=start_date, end_date__lte=end_date
        )

        events_data = [
            {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "location": event.location.name,
                "price": event.price,
                "category": event.category.name,
                "url_events_edit_event": reverse('events:edit-event', kwargs={'pk': event.id})
            }
            for event in events
        ]

        return JsonResponse({"events": events_data})
