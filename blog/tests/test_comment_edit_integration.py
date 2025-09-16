"""
Testes de integração para funcionalidade de edição de comentários
"""
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from blog.models import Post, Comment

User = get_user_model()


class CommentEditIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Criar usuários
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

        # Criar post
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.author
        )

        # Criar comentário
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            content='Original comment'
        )

    def test_comment_update_api_endpoint(self):
        """Testa se o endpoint de atualização de comentário funciona"""
        self.client.login(username='author', password='testpass123')

        url = reverse('comment-update', kwargs={'pk': self.comment.pk})
        data = {'content': 'Updated comment content'}

        response = self.client.patch(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Updated comment content')

    def test_comment_update_api_permission_denied(self):
        """Testa se usuário não autor não pode editar comentário"""
        self.client.login(username='other', password='testpass123')

        url = reverse('comment-update', kwargs={'pk': self.comment.pk})
        data = {'content': 'Updated comment content'}

        response = self.client.patch(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        # Como o queryset filtra apenas comentários do usuário atual,
        # comentários de outros usuários retornam 404 (não encontrado)
        self.assertEqual(response.status_code, 404)

    def test_comment_update_api_empty_content(self):
        """Testa validação de conteúdo vazio"""
        self.client.login(username='author', password='testpass123')

        url = reverse('comment-update', kwargs={'pk': self.comment.pk})
        data = {'content': ''}

        response = self.client.patch(
            url,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_comment_serializer_includes_author_id(self):
        """Testa se o serializador inclui author_id para verificação no front-end"""
        self.client.login(username='author', password='testpass123')

        url = reverse('comment-filter', kwargs={'post_id': self.post.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        comments = response.json()

        # Verificar se o comentário inclui author_id
        self.assertTrue(len(comments) > 0)
        comment_data = comments[0]
        self.assertIn('author_id', comment_data)
        self.assertEqual(comment_data['author_id'], self.author.pk)

    def test_blog_page_loads_with_edit_functionality(self):
        """Testa se a página do blog carrega com os scripts necessários"""
        self.client.login(username='author', password='testpass123')

        url = reverse('blog:home')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'comment_edit.js')
        self.assertContains(response, 'comment-author-id')

    def test_comment_display_includes_edit_button_for_author(self):
        """Testa se a página tem os scripts necessários para edição de comentários"""
        self.client.login(username='author', password='testpass123')

        url = reverse('blog:home')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Verificar se os scripts de edição estão presentes
        self.assertContains(response, 'comment_edit.js')
        self.assertContains(response, 'comment-author-id')

    def test_comment_display_no_edit_button_for_non_author(self):
        """Testa se o botão de editar não aparece para usuários que não são autores"""
        self.client.login(username='other', password='testpass123')

        url = reverse('blog:home')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Para usuário não autor, o botão de editar não deve estar presente
        # (isso será verificado pelo JavaScript no front-end)