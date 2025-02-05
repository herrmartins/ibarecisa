from django.http import JsonResponse
from django.views import View
from worship.models import Hymnal

class HymnalListView(View):
    def get(self, request):
        query = request.GET.get("q", "")
        hymnals = Hymnal.objects.filter(title__icontains=query)[:10]
        data = [{"id": hymnal.id, "text": hymnal.title} for hymnal in hymnals]
        return JsonResponse({"results": data})