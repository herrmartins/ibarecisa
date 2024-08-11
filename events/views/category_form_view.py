from events.models import EventCategory
from django.views.generic import FormView
from events.forms import EventCategoryForm
from django.contrib.auth.mixins import PermissionRequiredMixin


class CategoryFormView(PermissionRequiredMixin, FormView):
    permission_required = "events.add_event"
    template_name = "events/category_form.html"
    form_class = EventCategoryForm
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = EventCategory.objects.all()
        return context
