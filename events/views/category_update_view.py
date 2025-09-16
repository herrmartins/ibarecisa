from django.views.generic import UpdateView
from events.models import EventCategory
from events.forms import EventCategoryForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
import reversion


class CategoryUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "events.add_event"
    model = EventCategory
    form_class = EventCategoryForm
    template_name = "events/category_form.html"
    context_object_name = "category"
    success_url = reverse_lazy("events:create-event")

    def form_valid(self, form):
        with reversion.create_revision():
            reversion.set_user(self.request.user)
            return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = EventCategory.objects.all()
        return context
