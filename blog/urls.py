from django.urls import path
from blog.views import (
    BlogHomeView,
    PostFormView,
    PostCreateView,
    CategoryFormView,
    CategoryCreateView,
    PostUpdateView,
    CategoryUpdateView,
    CategoryDeleteView,
)

app_name = "blog"

urlpatterns = [
    path("", BlogHomeView.as_view(), name="home"),
    path("create", PostCreateView.as_view(), name="create-post"),
    path("update/<int:pk>", PostUpdateView.as_view(), name="update-post"),
    path("edit/<int:pk>", PostFormView.as_view(), name="edit"),
    path("form/category", CategoryFormView.as_view(), name="category-form"),
    path("create/category", CategoryCreateView.as_view(), name="create-category"),
    path("edit/category/<int:pk>",
         CategoryUpdateView.as_view(), name="edit-category"),
    path(
        "update/category/<int:pk>",
        CategoryUpdateView.as_view(), name="update-category"
    ),
    path(
        "category/delete/<int:pk>",
        CategoryDeleteView.as_view(), name="delete-category"
    ),
]
