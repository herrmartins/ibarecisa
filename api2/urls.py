from django.urls import path
from api2 import views

urlpatterns = [
    path("comments/add/<int:post_id>/",
         views.CommentCreateAPIView.as_view(), name="comment-create"),
    path("comments/update/<int:pk>/",
         views.CommentUpdateAPIView.as_view(), name="comment-update"),
    path("comments/delete/<int:pk>/",
         views.CommentDeleteAPIView.as_view(), name="comment-delete"),
    path("comments/<int:post_id>/",
         views.CommentListAPIView.as_view(), name="comment-filter"),
]
