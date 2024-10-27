from django.views.generic import TemplateView


class WorshipHomeView(TemplateView):
    template_name = 'worship/worship_home.html'