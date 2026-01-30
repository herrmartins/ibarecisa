from django.views.generic import FormView
from secretarial.forms import MinuteModelForm
from secretarial.models import MinuteProjectModel, MinuteTemplateModel
from secretarial.models import MinuteExcerptsModel
from django.shortcuts import redirect
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages


class CreateMinuteFormView(PermissionRequiredMixin, FormView):
    permission_required = "secretarial.add_meetingminutemodel"
    template_name = "secretarial/minute_creation.html"
    form_class = MinuteModelForm

    def get_initial(self):
        initial = super().get_initial()
        if "project_pk" in self.kwargs:
            try:
                minute_data = MinuteProjectModel.objects.get(
                    pk=self.kwargs.get("project_pk")
                )
                initial["president"] = minute_data.president
                initial["secretary"] = minute_data.secretary
                initial["meeting_date"] = minute_data.meeting_date.isoformat()
                initial["number_of_attendees"] = minute_data.number_of_attendees
                initial["body"] = minute_data.body
            except MinuteProjectModel.DoesNotExist:
                # Handle the case where the project PK does not exist
                return redirect("secretarial:home")

        elif "template_pk" in self.kwargs:
            try:
                minute_data = MinuteTemplateModel.objects.get(
                    pk=self.kwargs.get("template_pk")
                )
                initial["body"] = minute_data.body
                initial["agenda"] = minute_data.agenda.values_list('id', flat=True)
            except MinuteTemplateModel.DoesNotExist:
                # Handle the case where the template PK does not exist
                return redirect("secretarial:home")

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["excerpts_list"] = MinuteExcerptsModel.objects.all().order_by(
            "-times_used"
        )

        return context

    def form_valid(self, form):
        try:
            form.save()
            messages.success(self.request, "Ata criada com sucesso!")
            return redirect('secretarial:list-minutes')
        except Exception as e:
            messages.error(self.request, f"Erro ao criar ata: {e}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Por favor, corrija os erros abaixo.")
        return super().form_invalid(form)
