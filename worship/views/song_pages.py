from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.urls import reverse
from django.views.generic import CreateView, ListView

from worship.forms import SongForm
from worship.models import Composer, Hymnal, Song, SongTheme


def _is_worship_member(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff or user.type == "REGULAR"


class WorshipAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return _is_worship_member(self.request.user)


class SongListView(WorshipAccessMixin, ListView):
    template_name = "worship/song_list.html"
    model = Song
    context_object_name = "songs"

    def get_queryset(self):
        queryset = Song.objects.select_related("artist", "hymnal").prefetch_related("themes").all()
        q = self.request.GET.get("q", "").strip()
        composer = self.request.GET.get("composer", "").strip()
        theme = self.request.GET.get("theme", "").strip()
        hymnal = self.request.GET.get("hymnal", "").strip()

        if q:
            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(artist__name__icontains=q)
                | Q(lyrics__icontains=q)
            )
        if composer:
            queryset = queryset.filter(artist_id=composer)
        if theme:
            queryset = queryset.filter(themes__id=theme)
        if hymnal:
            queryset = queryset.filter(hymnal_id=hymnal)
        return queryset.distinct().order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["composers"] = Composer.objects.order_by("name").values_list("id", "name")
        context["themes"] = SongTheme.objects.order_by("title")
        context["hymnals"] = Hymnal.objects.order_by("title")
        context["filters"] = {
            "q": self.request.GET.get("q", "").strip(),
            "composer": self.request.GET.get("composer", "").strip(),
            "theme": self.request.GET.get("theme", "").strip(),
            "hymnal": self.request.GET.get("hymnal", "").strip(),
        }
        return context


class SongCreateView(WorshipAccessMixin, CreateView):
    template_name = "worship/song_form.html"
    form_class = SongForm
    model = Song

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Canção cadastrada com sucesso.")
        return response

    def get_success_url(self):
        return reverse("worship:song-detail", kwargs={"pk": self.object.pk})
