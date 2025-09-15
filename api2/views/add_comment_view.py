from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api2.serializers import CommentSerializer


class CommentCreateAPIView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id')
        data = request.data.copy()

        print("DEBUG - Received data:", dict(data))
        print("DEBUG - Post ID:", post_id)
        print("DEBUG - User:", request.user)

        # Extract only the fields we need for the serializer
        parent_value = data.get('parent')
        if parent_value:
            try:
                parent_value = int(parent_value)
            except (ValueError, TypeError):
                parent_value = None

        content = data.get('content', '').strip()
        if not content:
            print("ERRO: Content is empty")
            return Response({'content': ['Este campo é obrigatório.']}, status=status.HTTP_400_BAD_REQUEST)

        serializer_data = {
            'content': content,
            'parent': parent_value
        }

        print("DEBUG - Serializer data:", serializer_data)

        serializer = self.get_serializer(data=serializer_data)
        if serializer.is_valid():
            comment = serializer.save(author=request.user, post_id=post_id)
            print("DEBUG - Comment created successfully:", comment.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print("ERRO:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
