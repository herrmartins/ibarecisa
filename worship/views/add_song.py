from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from worship.models import Song, Composer, SongTheme

@method_decorator(csrf_exempt, name='dispatch')
class SongAddView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            title = data.get('title')
            artist_name = data.get('artist')
            theme_title = data.get('theme')
            lyrics = data.get('lyrics')

            print("DADOS:", data)
            
            if not title or not artist_name:
                return JsonResponse({"success": False, "error": "Title and artist are required."}, status=400)

            artist, _ = Composer.objects.get_or_create(name=artist_name)
            theme, _ = SongTheme.objects.get_or_create(title=theme_title)

            song = Song.objects.create(
                title=title,
                artist=artist,
                lyrics=lyrics
            )
            song.themes.add(theme)

            return JsonResponse({"success": True, "song_id": song.id})
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data."}, status=400)
