from django.views.generic import TemplateView


class AboutView(TemplateView):
    template_name = 'core/about.html'
