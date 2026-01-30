from django.views.generic import CreateView
from secretarial.forms import MinuteTemplateModelForm
from secretarial.models import MinuteTemplateModel
from secretarial.models import MinuteExcerptsModel
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy


class TemplateCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "secretarial.add_meetingminutemodel"
    form_class = MinuteTemplateModelForm
    template_name = "secretarial/template_form.html"
    context_object_name = "template"
    model = MinuteTemplateModel
    success_url = reverse_lazy('secretarial:list-templates')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["excerpts_list"] = MinuteExcerptsModel.objects.all().order_by(
            "-times_used")

        return context
