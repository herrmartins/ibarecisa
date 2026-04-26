from worship.models import Song, WorshipService, WorshipServiceSong
from django.views.generic import TemplateView


class WorshipHomeView(TemplateView):
    template_name = 'worship/worship_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['song_count'] = Song.objects.count()
        context['service_count'] = WorshipService.objects.count()
        context['pending_count'] = WorshipServiceSong.objects.filter(
            resolution_status=WorshipServiceSong.RESOLUTION_PENDING_REVIEW
        ).count()
        context['recent_songs'] = Song.objects.select_related('artist', 'hymnal').order_by('-id')[:8]
        context['recent_services'] = WorshipService.objects.order_by('-service_date', '-id')[:5]
        return context
