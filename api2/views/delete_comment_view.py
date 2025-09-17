from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from blog.models import Comment
from django.core.exceptions import ObjectDoesNotExist


class CommentDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except ObjectDoesNotExist:
            return Response({'error': 'Comentário não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Verificar se o usuário atual é o autor do comentário
        if instance.author != request.user:
            return Response({'error': 'Você só pode excluir seus próprios comentários'}, status=status.HTTP_403_FORBIDDEN)

        # Excluir o comentário
        self.perform_destroy(instance)
        return Response({'message': 'Comentário excluído com sucesso'}, status=status.HTTP_200_OK)