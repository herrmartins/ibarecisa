from django.views.generic import CreateView
from secretarial.forms import MinuteProjectModelForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from secretarial.utils import make_minute


class CreateMinuteProjectView(PermissionRequiredMixin, CreateView):
    permission_required = "secretarial.add_meetingminutemodel"
    form_class = MinuteProjectModelForm
    template_name = "secretarial/minute_created.html"
    success_url = reverse_lazy("secretarial:minute-home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = MinuteProjectModelForm
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        form_data = form.cleaned_data
        print("NUMBER OF ATENDES", form_data["number_of_attendees"])
        # meeting_date_str = form_data["meeting_date"].strftime("%Y-%m-%d")
        self.object.body = make_minute(form_data)
        self.object.save()

        return response
