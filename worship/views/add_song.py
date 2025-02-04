from django.http import JsonResponse
from django.views import View
import json
from worship.models import Song, Composer, SongTheme

class SongAddView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            title = data.get('title')
            artist_id = data.get('artist')  # Expecting an ID
            theme_id = data.get('theme')  # Expecting a single ID now
            lyrics = data.get('lyrics')
            metrics = data.get('metrics')
            key = data.get('key')

            print("DADOS:", data)

            # Validate required fields
            if not title or not artist_id:
                return JsonResponse(
                    {"success": False, "error": "Compositor e título são requeridos..."},
                    status=400
                )

            # Get the artist by ID
            try:
                artist = Composer.objects.get(id=artist_id)
            except Composer.DoesNotExist:
                return JsonResponse({"success": False, "error": "Compositor não encontrado."}, status=400)

            # Get the theme by ID (if provided)
            theme = None
            if theme_id:
                try:
                    theme = SongTheme.objects.get(id=theme_id)
                except SongTheme.DoesNotExist:
                    return JsonResponse({"success": False, "error": "Tema não encontrado."}, status=400)

            # Create the song
            song = Song.objects.create(
                title=title,
                artist=artist,
                lyrics=lyrics,
                metrics=metrics,
                key=key
            )

            # Associate the single theme
            if theme:
                song.themes.add(theme)

            return JsonResponse({"success": True, "song_id": song.id})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data."}, status=400)
