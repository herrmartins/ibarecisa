from django.http import JsonResponse
from django.views import View
from django.utils.dateparse import parse_date
from .models import Event


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
                "title": event.title,
                "description": event.description,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "location": event.location.name,
            }
            for event in events
        ]

        return JsonResponse({"events": events_data})
