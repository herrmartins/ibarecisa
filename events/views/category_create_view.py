from django.views.generic import CreateView
from events.models import EventCategory
from events.forms import EventCategoryForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy


class CategoryCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "events.add_event"
    model = EventCategory
    form_class = EventCategoryForm
    template_name = "events/category_form.html"
    success_url = reverse_lazy("events:create-event")
