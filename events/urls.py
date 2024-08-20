from django.urls import path
from events.views import (
    EventsHomeView,
    EventsFormView,
    EventCreateView,
    EventUpdateView,
    VenueCreateView,
    VenueFormView,
    VenuesListView,
    VenueUpdateView,
    CategoryUpdateView,
    CategoryFormView,
    CategoryCreateView,
    EventsByPeriodView,
)

app_name = "events"

urlpatterns = [
    path("", EventsHomeView.as_view(), name="home"),
    path("venues/list", VenuesListView.as_view(), name="venues-list"),
    path("register", EventsFormView.as_view(), name="register"),
    path("edit/<int:pk>", EventsFormView.as_view(), name="edit-event"),
    path("create", EventCreateView.as_view(), name="create-event"),
    path("update/<int:pk>", EventUpdateView.as_view(), name="update-event"),
    path("venues/register", VenueFormView.as_view(), name="register-venue"),
    path("venues/edit/<int:pk>", VenueFormView.as_view(), name="edit-venue"),
    path("venues/create", VenueCreateView.as_view(), name="create-venue"),
    path("venues/update/<int:pk>", VenueUpdateView.as_view(), name="update-venue"),
    path(
        "category",
        CategoryFormView.as_view(),
        name="category-form",
    ),
    path(
        "category/edit/<int:pk>",
        CategoryUpdateView.as_view(),
        name="edit-category",
    ),
    path(
        "category/create",
        CategoryCreateView.as_view(),
        name="create-category",
    ),
    path(
        "category/update/<int:pk>",
        CategoryUpdateView.as_view(),
        name="update-category",
    ),
    path("byperiod", EventsByPeriodView.as_view(), name="events-by-period-ajax"),
]
