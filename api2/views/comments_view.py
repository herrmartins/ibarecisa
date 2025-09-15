from api2.serializers import CommentSerializer
from rest_framework import generics
from blog.models import Comment


class CommentListAPIView(generics.ListAPIView):
    serializer_class = CommentSerializer
    lookup_field = 'post_id'

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        if post_id:
            queryset = Comment.objects.filter(
                post=post_id).order_by("created")
        else:
            queryset = Comment.objects.none()
        return queryset
