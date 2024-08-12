from django.urls import path
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordResetCompleteView)
from users.views import (
    UserProfileView,
    UserProfileUpdateView,
    RegisterFormView,
    ChangeUserPasswordView,
    UpdateUserTypeView,
    UpdateUserFunctionView,
)


app_name = "users"

urlpatterns = [
    path("register", RegisterFormView.as_view(), name="register"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("profile/<int:pk>", UserProfileView.as_view(), name="user-profile"),
    path(
        "profile/update/<int:pk>",
        UserProfileUpdateView.as_view(),
        name="user-profile-update",
    ),
    path(
        "profile/change_password",
        ChangeUserPasswordView.as_view(),
        name="change-user-password",
    ),
    path("update/<int:pk>", UpdateUserTypeView.as_view(), name="update-user-type"),
    path(
        "update/function/<int:pk>",
        UpdateUserFunctionView.as_view(),
        name="update-user-functions",
    ),

    path("password/reset", PasswordResetView.as_view(), name="reset-password"),
    path("password/<uidb64>/<token>/", PasswordResetConfirmView.as_view(),
         name="confirm-reset-password"),
    path("password/complete", PasswordResetCompleteView.as_view(),
         name="complete-reset-password"),
]
