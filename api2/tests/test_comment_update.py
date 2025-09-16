from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from blog.models import Comment, Post
from users.models import CustomUser

User = get_user_model()


class CommentUpdateAPITestCase(APITestCase):
    def setUp(self):
        # Criar usuários de teste
        self.author = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123'
        )

        # Criar post de teste
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.author
        )

        # Criar comentário de teste
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            content='Original comment content'
        )

    def test_update_comment_success(self):
        """Teste de atualização bem-sucedida de comentário pelo autor"""
        self.client.force_authenticate(user=self.author)

        url = reverse('comment-update', kwargs={'pk': self.comment.pk})
        data = {'content': 'Updated comment content'}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Updated comment content')

    def test_update_comment_unauthorized(self):
        """Teste de tentativa de atualização por usuário não autor"""
        self.client.force_authenticate(user=self.other_user)

        url = reverse('comment-update', kwargs={'pk': self.comment.pk})
        data = {'content': 'Updated comment content'}

        response = self.client.patch(url, data, format='json')

        # Como o queryset filtra apenas comentários do usuário atual,
        # comentários de outros usuários retornam 404 (não encontrado)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_comment_not_authenticated(self):
        """Teste de tentativa de atualização sem autenticação"""
        url = reverse('comment-update', kwargs={'pk': self.comment.pk})
        data = {'content': 'Updated comment content'}

        response = self.client.patch(url, data, format='json')

        # Django pode retornar 403 (Forbidden) ao invés de 401 quando não autenticado
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_update_comment_empty_content(self):
        """Teste de atualização com conteúdo vazio"""
        self.client.force_authenticate(user=self.author)

        url = reverse('comment-update', kwargs={'pk': self.comment.pk})
        data = {'content': ''}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)

    def test_update_comment_whitespace_content(self):
        """Teste de atualização com conteúdo apenas espaços em branco"""
        self.client.force_authenticate(user=self.author)

        url = reverse('comment-update', kwargs={'pk': self.comment.pk})
        data = {'content': '   '}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)

    def test_update_comment_not_found(self):
        """Teste de atualização de comentário inexistente"""
        self.client.force_authenticate(user=self.author)

        url = reverse('comment-update', kwargs={'pk': 9999})
        data = {'content': 'Updated content'}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_comment_partial_update(self):
        """Teste de atualização parcial (PATCH)"""
        self.client.force_authenticate(user=self.author)

        url = reverse('comment-update', kwargs={'pk': self.comment.pk})
        data = {'content': 'Partially updated content'}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Partially updated content')

    def test_update_comment_preserves_other_fields(self):
        """Teste para garantir que outros campos não sejam afetados"""
        self.client.force_authenticate(user=self.author)

        original_author = self.comment.author
        original_post = self.comment.post
        original_created = self.comment.created

        url = reverse('comment-update', kwargs={'pk': self.comment.pk})
        data = {'content': 'Updated content'}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()

        # Verificar que outros campos não mudaram
        self.assertEqual(self.comment.author, original_author)
        self.assertEqual(self.comment.post, original_post)
        self.assertEqual(self.comment.created, original_created)
        self.assertEqual(self.comment.content, 'Updated content')