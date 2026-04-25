from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from worship.forms import ComposerQuickForm, HymnalQuickForm, SongThemeQuickForm
from worship.models import Composer, Hymnal, SongTheme


def _is_worship_member(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff or user.type == "REGULAR"


class WorshipAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return _is_worship_member(self.request.user)


class WorshipCatalogSettingsView(WorshipAccessMixin, TemplateView):
    template_name = "worship/catalog_settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["composer_form"] = kwargs.get("composer_form") or ComposerQuickForm()
        context["hymnal_form"] = kwargs.get("hymnal_form") or HymnalQuickForm()
        context["theme_form"] = kwargs.get("theme_form") or SongThemeQuickForm()
        context["recent_composers"] = Composer.objects.order_by("name")[:12]
        context["recent_hymnals"] = Hymnal.objects.order_by("title")[:12]
        context["recent_themes"] = SongTheme.objects.order_by("title")[:20]
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "")

        if action == "add_composer":
            form = ComposerQuickForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Compositor cadastrado com sucesso.")
                return redirect("worship:catalog-settings")
            return self.render_to_response(self.get_context_data(composer_form=form))

        if action == "add_hymnal":
            form = HymnalQuickForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Hinário cadastrado com sucesso.")
                return redirect("worship:catalog-settings")
            return self.render_to_response(self.get_context_data(hymnal_form=form))

        if action == "add_theme":
            form = SongThemeQuickForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Tema cadastrado com sucesso.")
                return redirect("worship:catalog-settings")
            return self.render_to_response(self.get_context_data(theme_form=form))

        messages.error(request, "Ação inválida.")
        return redirect("worship:catalog-settings")
