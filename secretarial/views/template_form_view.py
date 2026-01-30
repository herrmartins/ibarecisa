from django.views.generic import FormView
from secretarial.forms import MinuteTemplateModelForm
from secretarial.models import MinuteExcerptsModel, MinuteTemplateModel
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages


class TemplateFormView(PermissionRequiredMixin, FormView):
    permission_required = "secretarial.add_meetingminutemodel"
    template_name = 'secretarial/template_form.html'
    form_class = MinuteTemplateModelForm

    def dispatch(self, request, *args, **kwargs):
        # Check if the object exists for update (for both GET and POST)
        self.object = get_object_or_404(
            MinuteTemplateModel, pk=kwargs.get('pk')) if 'pk' in kwargs else None
        self.pk = kwargs.get('pk')
        self.is_update = self.object is not None
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.object:
            initial["title"] = self.object.title
            initial["body"] = self.object.body
            initial["agenda"] = self.object.agenda
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["excerpts_list"] = MinuteExcerptsModel.objects.all().order_by(
            "-times_used")
        context["pk"] = self.pk
        context["template_object"] = self.object
        return context

    def form_valid(self, form):
        if self.is_update:
            template = self.object
            template.title = form.cleaned_data['title']
            template.body = form.cleaned_data['body']
            template.agenda = form.cleaned_data['agenda']
            template.save()
            messages.success(self.request, "Modelo atualizado com sucesso!")
        else:
            form.save()
            messages.success(self.request, "Modelo criado com sucesso!")
        return redirect('secretarial:list-templates')

    def form_invalid(self, form):
        messages.error(self.request, "Por favor, corrija os erros abaixo.")
        return super().form_invalid(form)
