from django.views.generic import FormView
from secretarial.forms import MinuteTemplateModelForm
from secretarial.models import MinuteExcerptsModel, MinuteTemplateModel
from django.contrib.auth.mixins import PermissionRequiredMixin


class TemplateFormView(PermissionRequiredMixin, FormView):
    permission_required = "secretarial.add_meetingminutemodel"
    template_name = 'secretarial/template_form.html'
    form_class = MinuteTemplateModelForm

    def get_initial(self):
        initial = super().get_initial()
        if 'pk' in self.kwargs:
            template_data = MinuteTemplateModel.objects.get(
                pk=self.kwargs.get("pk"))
            initial["title"] = template_data.title
            initial["body"] = template_data.body
            initial["agenda"] = template_data.agenda
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["excerpts_list"] = MinuteExcerptsModel.objects.all().order_by(
            "-times_used")

        return context
