from django.urls import path
from api2 import views

urlpatterns = [
    path("comments/<int:post_id>",
         views.CommentListAPIView.as_view(), name="comment-filter"),
    path("comments/add/<int:post_id>",
         views.CommentCreateAPIView.as_view(), name="comment-create"),
]
