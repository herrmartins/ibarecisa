from worship.models import Composer, SongTheme, Hymnal
from django.views.generic import TemplateView


class WorshipHomeView(TemplateView):
    template_name = 'worship/worship_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['composers'] = Composer.objects.all()
        context['themes'] = SongTheme.objects.all()
        hymnals = list(Hymnal.objects.values('id', 'title'))
        context['hymnals'] = hymnals
        return context