from django.views.generic import DetailView
from worship.models import Song

class SongDetailView(DetailView):
    model = Song
    template_name = 'worship/song_detail.html'
    context_object_name = 'song'
