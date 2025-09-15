from rest_framework import serializers
from blog.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(
        source='author.get_full_name', read_only=True)
    user_photo = serializers.ImageField(
        source='author.profile_image', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'parent',
                  'likes', 'created', 'user_photo', 'author_name']
        read_only_fields = ['id', 'post', 'author', 'created', 'likes', 'user_photo', 'author_name']
