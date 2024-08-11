from django.views.generic import FormView
from secretarial.forms import MinuteExcerptsModelForm
from secretarial.models import MinuteExcerptsModel
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import PermissionRequiredMixin


class ExcerptsFormView(PermissionRequiredMixin, FormView):
    permission_required = "secretarial.add_meetingminutemodel"
    template_name = "secretarial/update_excerpt.html"
    form_class = MinuteExcerptsModelForm

    def get(self, request, *args, **kwargs):
        # Check if the object exists for update
        self.object = (
            get_object_or_404(MinuteExcerptsModel, pk=kwargs.get("pk"))
            if "pk" in kwargs
            else None
        )

        # Set the context variable to determine the mode
        self.is_update = self.object is not None
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = self.is_update
        context["pk"] = self.kwargs.get("pk")
        return context

    def get_initial(self):
        initial = super().get_initial()
        if "pk" in self.kwargs:
            excerpt_data = MinuteExcerptsModel.objects.get(pk=self.kwargs.get("pk"))
            initial["title"] = excerpt_data.title
            initial["excerpt"] = excerpt_data.excerpt
        return initial
