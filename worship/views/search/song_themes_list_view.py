from django.http import JsonResponse
from django.views import View
from worship.models import SongTheme

class ThemeListView(View):
    def get(self, request):
        query = request.GET.get("q", "")
        themes = SongTheme.objects.filter(title__icontains=query)[:10]
        
        data = [{"id": theme.id, "text": theme.title} for theme in themes]
        
        return JsonResponse({"results": data})
