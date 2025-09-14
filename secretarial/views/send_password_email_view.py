from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin

from users.utils.send_message import send_message

CustomUser = get_user_model()


class SendPasswordEmailView(PermissionRequiredMixin, View):
    permission_required = 'users.add_customuser'

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)

        if not user.email:
            messages.error(
                request,
                f"Não é possível enviar senha para {user.get_full_name()}: e-mail não cadastrado."
            )
            return redirect('secretarial:users-qualifying')

        if user.has_usable_password():
            messages.warning(
                request,
                f"{user.get_full_name()} já possui senha. Use a opção 'Esqueci minha senha' se necessário."
            )
            return redirect('secretarial:users-qualifying')

        try:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            current_site = get_current_site(request)
            reset_url = f"http://{current_site.domain}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"

            subject = "Bem-vindo à IBARECISA - Defina sua senha"
            message = f"""
                            Olá {user.first_name},

                            Você foi cadastrado como membro da IBARECISA e agora pode acessar o sistema.

                            Para definir sua senha e ter acesso completo, clique no link abaixo:
                            {reset_url}

                            Este link é válido por 7 dias.

                            Se você não solicitou este acesso, ignore este e-mail.

                            Atenciosamente,
                            Equipe IBARECISA
                        """

            send_message(subject, message, [user.email])

            messages.success(
                request,
                f"E-mail de definição de senha enviado com sucesso para {user.get_full_name()}."
            )

        except Exception as e:
            messages.error(
                request,
                f"Erro ao enviar e-mail para {user.get_full_name()}: {str(e)}"
            )

        return redirect('secretarial:users-qualifying')