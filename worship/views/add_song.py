from django.http import JsonResponse
from django.views import View
import json
from worship.models import Song, Composer, SongTheme

class SongAddView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            title = data.get('title')
            artist_name = data.get('artist')
            theme_title = data.get('theme')
            lyrics = data.get('lyrics')
            metrics = data.get('metrics')
            key = data.get('key')

            print("DADOS:", data)
            
            if not title or not artist_name:
                return JsonResponse({"success": False, "error": "Compositor e título são requeridos..."}, status=400)

            artist, _ = Composer.objects.get_or_create(name=artist_name)
            theme, _ = SongTheme.objects.get_or_create(title=theme_title)

            song = Song.objects.create(
                title=title,
                artist=artist,
                lyrics=lyrics,
                metrics=metrics,
                key=key
            )
            song.themes.add(theme)

            return JsonResponse({"success": True, "song_id": song.id})
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data."}, status=400)
