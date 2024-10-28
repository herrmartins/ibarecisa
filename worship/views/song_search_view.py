from django.http import JsonResponse
from django.views.generic import View
from django.db.models import Q
from worship.models import Song
import re


class SongSearchView(View):
    def get(self, request):
        query = request.GET.get("q", "")

        # Perform separate searches for each category
        results_by_title = Song.objects.filter(title__icontains=query).distinct()[:5]
        results_by_artist = Song.objects.filter(
            artist__name__icontains=query
        ).distinct()[:5]
        results_by_lyrics = Song.objects.filter(lyrics__icontains=query).distinct()[:5]
        results_by_theme = Song.objects.filter(
            themes__title__icontains=query
        ).distinct()[
            :5
        ]  # assuming 'themes' is a ManyToManyField to SongTheme

        # Organize results into a grouped JSON response
        data = {
            "title_matches": [
                {
                    "id": song.id,
                    "title": song.title,
                    "artist": song.artist.name if song.artist else "Desconhecido",
                }
                for song in results_by_title
            ],
            "artist_matches": [
                {
                    "id": song.id,
                    "title": song.title,
                    "artist": song.artist.name if song.artist else "Desconhecido",
                }
                for song in results_by_artist
            ],
            "lyrics_matches": [
                {
                    "id": song.id,
                    "title": song.title,
                    "artist": song.artist.name if song.artist else "Desconhecido",
                    "snippet": (
                        lambda lyrics: (
                            re.sub(
                                f"({query})", r"<strong>\1</strong>",
                                re.search(f"(.{{0,50}}{query}.{{0,50}})", lyrics, re.IGNORECASE).group(1),
                                flags=re.IGNORECASE
                            )
                            if re.search(f"{query}", lyrics, re.IGNORECASE)
                            else "Desconhecido"
                        )
                    )(song.lyrics) if song.lyrics else "Desconhecido",
                }
                for song in results_by_lyrics
            ],
            "theme_matches": [
                {
                    "id": song.id,
                    "title": song.title,
                    "theme": (
                        [theme.title for theme in song.themes.all()]
                        if song.themes.exists()
                        else ["Desconhecido"]
                    ),
                }
                for song in results_by_theme
            ],
        }

        return JsonResponse(data, safe=False)
