from django.http import JsonResponse
from django.views import View
from worship.models import SongTheme

class ThemeListView(View):
    def get(self, request):
        query = request.GET.get("q", "")
        
        if query:
            themes = SongTheme.objects.filter(title__icontains=query)
        else:
            themes = SongTheme.objects.all()

        themes = themes[:50]

        data = [{"id": theme.id, "text": theme.title} for theme in themes]
        return JsonResponse({"results": data})

