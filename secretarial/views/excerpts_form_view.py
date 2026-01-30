from django.views.generic import FormView
from secretarial.forms import MinuteExcerptsModelForm
from secretarial.models import MinuteExcerptsModel
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages


class ExcerptsFormView(PermissionRequiredMixin, FormView):
    permission_required = "secretarial.add_meetingminutemodel"
    template_name = 'secretarial/update_excerpt.html'
    form_class = MinuteExcerptsModelForm

    def dispatch(self, request, *args, **kwargs):
        # Check if the object exists for update (for both GET and POST)
        self.object = get_object_or_404(
            MinuteExcerptsModel, pk=kwargs.get('pk')) if 'pk' in kwargs else None
        self.is_update = self.object is not None
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = self.is_update
        context['pk'] = self.kwargs.get('pk')
        context['excerpt_object'] = self.object
        return context

    def get_initial(self):
        initial = super().get_initial()
        if 'pk' in self.kwargs:
            excerpt_data = MinuteExcerptsModel.objects.get(
                pk=self.kwargs.get("pk"))
            initial["title"] = excerpt_data.title
            initial["excerpt"] = excerpt_data.excerpt
        return initial

    def form_valid(self, form):
        # Save the form
        if self.is_update:
            excerpt = self.object
            excerpt.title = form.cleaned_data['title']
            excerpt.excerpt = form.cleaned_data['excerpt']
            excerpt.save()
            messages.success(self.request, "Trecho atualizado com sucesso!")
        else:
            form.save()
            messages.success(self.request, "Trecho criado com sucesso!")
        # Redirect to excerpts list instead of showing detail page
        return redirect('secretarial:list-excerpts')

    def form_invalid(self, form):
        messages.error(self.request, "Por favor, corrija os erros abaixo.")
        return super().form_invalid(form)
