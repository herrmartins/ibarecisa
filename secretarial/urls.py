from django.urls import path
from secretarial.views import (
    SecretarialHomeView,
    MinutesEditorView,
    UsersQualifyingListView,
    UserDetailQualifyingView,
    MinuteHomeView,
    CreateMinuteProjectView,
    MinutesProjectListView,
    MinuteCreateView,
    CreateMinuteFormView,
    MinuteDetailView,
    MinutesListView,
    MinutesExcerptsListView,
    MinuteTemplatesListView,
    ExcerptCreateView,
    ExcerptUpdateView,
    ExcerptsFormView,
    ExcerptDetailView,
    ExcerptDeleteView,
    GeneratePDF,
    TemplateCreateView,
    TemplateFormView,
    AgendaFormView,
    AgendaCreateView,
)


app_name = "secretarial"

urlpatterns = [
    path("", SecretarialHomeView.as_view(), name="home"),
    path("minute", MinutesEditorView.as_view(), name="minutes-editor"),
    path("users", UsersQualifyingListView.as_view(), name="users-qualifying"),
    path("user/<int:pk>", UserDetailQualifyingView.as_view(), name="user-qualify"),
    path("meeting", MinuteHomeView.as_view(), name="minute-home"),
    path("cmproject", CreateMinuteProjectView.as_view(),
         name="create-minute-project"),
    path(
        "meeting/projects",
        MinutesProjectListView.as_view(),
        name="list-minutes-projects",
    ),
    path("meeting/list", MinutesListView.as_view(), name="list-minutes"),
    path("meeting/excerpts", MinutesExcerptsListView.as_view(), name="list-excerpts"),
    path("meeting/templates", MinuteTemplatesListView.as_view(),
         name="list-templates"),
    path("meeting/templates/create",
         TemplateCreateView.as_view(), name="template-create"),
    path("meeting/template/form", TemplateFormView.as_view(), name="template-form"),
    path("meeting/template/form/<int:pk>",
         TemplateFormView.as_view(), name="template-update"),
    path(
        "create-minute/project/<int:project_pk>/",
        CreateMinuteFormView.as_view(),
        name="minute-creation-form-view",
    ),
    path(
        "create-minute/template/<int:template_pk>/",
        CreateMinuteFormView.as_view(),
        name="minute-from-template-view",
    ),
    path(
        "meeting/create-minute", MinuteCreateView.as_view(), name="create-minute-view"
    ),
    path(
        "meeting/detail/<int:pk>", MinuteDetailView.as_view(), name="minute-detail-view"
    ),
    path("meeting/genpdf/<int:pk>", GeneratePDF.as_view(),
         name="minute-generate-pdf"),
    path(
        "excerpts/form/<int:pk>", ExcerptsFormView.as_view(), name="excerpt-update-form"
    ),
    path("excerpts/form", ExcerptsFormView.as_view(), name="excerpt-form"),
    path("excerpt/create", ExcerptCreateView.as_view(), name="create-excerpt"),
    path("excerpt/update/<int:pk>",
         ExcerptUpdateView.as_view(), name="update-excerpt"),
    path("excerpt/<int:pk>", ExcerptDetailView.as_view(), name="excerpt-detail"),
    path(
        "excerpt/delete/<int:pk>",
        ExcerptDeleteView.as_view(),
        name="delete-excerpt",
    ),
    path("meeting/agenda", AgendaFormView.as_view(), name="agenda-form"),
    path("meeting/agenda/<int:pk>", AgendaFormView.as_view(), name="agenda-update"),
    path("meeting/agenda/create", AgendaCreateView.as_view(), name="agenda-create"),
]
