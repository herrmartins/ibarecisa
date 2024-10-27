from django.http import JsonResponse
from django.views.generic import View
from worship.models import Song
from django.db.models import Q

class SongSearchView(View):
    def get(self, request):
        query = request.GET.get("q", "")
        results = Song.objects.filter(
            Q(title__icontains=query) |
            Q(lyrics__icontains=query) |
            Q(themes__title__icontains=query) |
            Q(artist__name__icontains=query)
        ).distinct()[:5]
        data = [
            {
                "id": song.id,
                "title": song.title,
                "artist": song.artist.name if song.artist else "Unknown",
            }
            for song in results
        ]
        return JsonResponse(data, safe=False)
