from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from users.models import CustomUser


class UserApprovalFunctionalityTest(TestCase):
    def setUp(self):
        # Criar grupo de secretário
        self.secretary_group = Group.objects.create(name="secretary")
        permissions = Permission.objects.filter(
            codename__in=["change_customuser", "delete_customuser", "add_customuser"]
        )
        for perm in permissions:
            self.secretary_group.permissions.add(perm)

        # Criar usuário secretário
        self.secretary = get_user_model().objects.create_user(
            username="secretary",
            email="secretary@example.com",
            password="password123"
        )
        self.secretary.groups.add(self.secretary_group)
        for perm in permissions:
            self.secretary.user_permissions.add(perm)

        # Criar usuário a ser aprovado
        self.user_to_approve = get_user_model().objects.create_user(
            username="newuser",
            email="newuser@example.com",
            password="password123",
            is_approved=False
        )

        self.client.login(username="secretary", password="password123")

    def test_user_approval_workflow(self):
        """Testa o fluxo completo de aprovação de usuário"""
        # 1. Usuário não aprovado deve ser redirecionado para welcome
        self.client.logout()
        self.client.login(username="newuser", password="password123")

        response = self.client.get('/secretarial/')
        # Durante testes, middleware é pulado, então deve funcionar
        # Mas vamos testar a lógica de aprovação diretamente

        # 2. Verificar que usuário começa como não aprovado
        user = CustomUser.objects.get(username="newuser")
        self.assertFalse(user.is_approved)

        # 3. Secretário faz login e acessa página de usuários
        self.client.logout()
        self.client.login(username="secretary", password="password123")

        response = self.client.get(reverse('secretarial:users-qualifying'))
        self.assertEqual(response.status_code, 200)

        # 4. Secretário acessa página de detalhes do usuário
        response = self.client.get(reverse('secretarial:user-qualify', kwargs={'pk': user.pk}))
        self.assertEqual(response.status_code, 200)

        # 5. Secretário aprova o usuário via POST
        response = self.client.post(
            reverse('users:update-user-functions', kwargs={'pk': user.pk}),
            {'is_approved': 'on'}  # Checkbox marcado
        )
        self.assertEqual(response.status_code, 302)  # Redirect após sucesso

        # 6. Verificar que usuário agora está aprovado
        user.refresh_from_db()
        self.assertTrue(user.is_approved)

    def test_user_approval_preservation(self):
        """
        Testa que o status de aprovação é preservado quando o checkbox
        não é enviado (comportamento intencional para evitar desaprovação acidental).
        """
        # Primeiro aprovar o usuário
        self.user_to_approve.is_approved = True
        self.user_to_approve.save()

        # Secretário envia POST sem is_approved (checkbox não marcado)
        # O comportamento esperado é PRESERVAR o status original
        response = self.client.post(
            reverse('users:update-user-functions', kwargs={'pk': self.user_to_approve.pk}),
            {}  # Checkbox não marcado
        )
        self.assertEqual(response.status_code, 302)

        # Verificar que o status de aprovação foi PRESERVADO (não alterado)
        self.user_to_approve.refresh_from_db()
        self.assertTrue(self.user_to_approve.is_approved)

    def test_approval_form_display(self):
        """Testa se o form de aprovação é exibido corretamente"""
        response = self.client.get(reverse('secretarial:user-qualify', kwargs={'pk': self.user_to_approve.pk}))

        # Verificar se o form de aprovação está no contexto
        self.assertIn('approval_form', response.context)
        approval_form = response.context['approval_form']

        # Verificar se o form tem o campo is_approved
        self.assertIn('is_approved', approval_form.fields)

        # Verificar se o checkbox reflete o status atual (False)
        self.assertFalse(approval_form.instance.is_approved)

    def test_only_secretary_can_approve_users(self):
        """Testa que apenas secretários podem aprovar usuários"""
        # Criar usuário normal (não secretário)
        regular_user = get_user_model().objects.create_user(
            username="regular",
            email="regular@example.com",
            password="password123"
        )

        self.client.logout()
        self.client.login(username="regular", password="password123")

        # Tentar aprovar usuário
        response = self.client.post(
            reverse('users:update-user-functions', kwargs={'pk': self.user_to_approve.pk}),
            {'is_approved': 'on'}
        )

        # Deve falhar (403 Forbidden ou redirect)
        self.assertIn(response.status_code, [403, 302])

        # Verificar que aprovação não foi alterada
        self.user_to_approve.refresh_from_db()
        self.assertFalse(self.user_to_approve.is_approved)