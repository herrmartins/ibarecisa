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
    CategoryUpdateView,
    NewMinutesEditorView,
    MinuteProjectDeleteView,
    MinuteFileUploadView,
    MinuteProjectEditView,
    SendPasswordEmailView,
    MemberRegistrationView,
    PDFImportView,
)


app_name = "secretarial"

urlpatterns = [
    path("", SecretarialHomeView.as_view(), name="home"),
    path("minute", MinutesEditorView.as_view(), name="minutes-editor"),
    path("users", UsersQualifyingListView.as_view(), name="users-qualifying"),
    path("user/<int:pk>", UserDetailQualifyingView.as_view(), name="user-qualify"),
    path("user/<int:pk>/send-password", SendPasswordEmailView.as_view(), name="send-password-email"),
    path("member-registration", MemberRegistrationView.as_view(), name="member-registration"),
    path("meeting", MinuteHomeView.as_view(), name="minute-home"),
    path("cmproject", CreateMinuteProjectView.as_view(),
         name="create-minute-project"),
    path(
        "meeting/projects",
        MinutesProjectListView.as_view(),
        name="list-minutes-projects",
    ),
    path(
        "meeting/projects/delete/<int:pk>/",
        MinuteProjectDeleteView.as_view(),
        name="delete-minute-project",
    ),
    path(
        "meeting/projects/edit/<int:pk>/",
        MinuteProjectEditView.as_view(),
        name="edit-minute-project",
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
        "create-minute/template/new/",
        CreateMinuteFormView.as_view(),
        name="new-minute-view",
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
        "meeting/<int:minute_pk>/attachments/add",
        MinuteFileUploadView.as_view(),
        name="minute-attachment-add",
    ),
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
    path("meeting/agenda/<int:pk>", CategoryUpdateView.as_view(), name="agenda-update"),
    path("meeting/agenda/create", AgendaCreateView.as_view(), name="agenda-create"),
    path("meeting/pdf-import", PDFImportView.as_view(), name="pdf-import"),
    path("editor", NewMinutesEditorView.as_view(), name="new-minutes-editor"),
]
