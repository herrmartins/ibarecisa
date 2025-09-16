from rest_framework import serializers
from blog.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(
        source='author.get_full_name', read_only=True)
    user_photo = serializers.ImageField(
        source='author.profile_image', read_only=True)
    author_id = serializers.IntegerField(
        source='author.id', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_id', 'content', 'parent',
                  'likes', 'created', 'user_photo', 'author_name']
        read_only_fields = ['id', 'post', 'author', 'author_id', 'created', 'likes', 'user_photo', 'author_name']

    def update(self, instance, validated_data):
        # Verificar se o usuário atual é o autor do comentário
        if instance.author != self.context['request'].user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Você só pode editar seus próprios comentários.")

        # Atualizar apenas o campo content
        instance.content = validated_data.get('content', instance.content)
        instance.save()
        return instance
