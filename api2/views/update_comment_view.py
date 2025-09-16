from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api2.serializers import CommentSerializer
from blog.models import Comment


class CommentUpdateAPIView(generics.UpdateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Verificar se o usuário é o autor do comentário
        if instance.author != request.user:
            return Response(
                {'error': 'Você só pode editar seus próprios comentários.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validar apenas o campo content
        content = request.data.get('content', '').strip()
        if not content:
            return Response(
                {'content': ['Este campo é obrigatório.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Atualizar apenas o conteúdo
        instance.content = content
        instance.save()

        # Retornar o comentário atualizado
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)