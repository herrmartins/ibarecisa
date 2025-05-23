from django.views.generic import FormView
from secretarial.forms import MinuteModelForm
from secretarial.models import MinuteProjectModel, MinuteTemplateModel
from secretarial.models import MinuteExcerptsModel
from django.shortcuts import redirect
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect


class CreateMinuteFormView(PermissionRequiredMixin, FormView):
    permission_required = "secretarial.add_meetingminutemodel"
    template_name = "secretarial/minute_creation.html"
    form_class = MinuteModelForm

    def get_initial(self):
        initial = super().get_initial()

        if "project_pk" in self.kwargs:
            print("ESTOU NO PK")
            minute_data = MinuteProjectModel.objects.get(pk=self.kwargs["project_pk"])
            initial["president"] = minute_data.president
            initial["secretary"] = minute_data.secretary
            initial["meeting_date"] = minute_data.meeting_date.isoformat()
            initial["number_of_attendees"] = minute_data.number_of_attendees
            initial["body"] = minute_data.body
            initial["agenda"] = list(minute_data.meeting_agenda.values_list("pk", flat=True))

        elif "template_pk" in self.kwargs:
            print("ESTOU NO TEMPLATE")
            minute_data = MinuteTemplateModel.objects.get(pk=self.kwargs["template_pk"])
            initial["body"] = minute_data.body
            initial["agenda"] = list(minute_data.agenda.values_list("pk", flat=True))

        return initial


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
                initial["agenda"] = minute_data.meeting_agenda.all()
            except MinuteProjectModel.DoesNotExist:
                # Handle the case where the project PK does not exist
                return redirect("secretarial:home")

        elif "template_pk" in self.kwargs:
            try:
                minute_data = MinuteTemplateModel.objects.get(
                    pk=self.kwargs.get("template_pk")
                )
                initial["body"] = minute_data.body
                initial["agenda"] = minute_data.agenda.all()
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
