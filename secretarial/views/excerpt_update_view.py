from django.views.generic import UpdateView
from secretarial.models import MinuteExcerptsModel
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.contrib import messages


class ExcerptUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "secretarial.add_meetingminutemodel"
    model = MinuteExcerptsModel
    template_name = 'secretarial/update_excerpt.html'
    fields = ['title', 'excerpt']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        context['pk'] = self.object.pk
        return context

    def get_success_url(self):
        messages.success(self.request, "Trecho atualizado com sucesso!")
        return reverse("secretarial:list-excerpts")
