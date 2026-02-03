from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.conf import settings
from users.models import CustomUser
from users.forms import RegisterUserForm
from users.utils import send_message
import logging

logger = logging.getLogger(__name__)


class RegisterFormView(CreateView):
    model = CustomUser
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        message = f"Olá, {user.first_name}!\n    Estamos muito felizes em recebê-lo como usuário no site da IBARECISA. A partir de agora, você pode interagir conosco comentando nos posts do nosso blog. A sua opinião é muito importante para nós e estamos ansiosos para ouvir o que você tem a dizer! \nAlém disso, estamos trabalhando para expandir as funcionalidades do site. Em breve, você terá acesso a inscrições facilitadas em nossos eventos e receberá nossa newsletter (caso queira), com mensagens edificantes e novidades. \nObrigado por se juntar a nós. Se tiver qualquer dúvida ou sugestão, não hesite em entrar em contato. \nCom carinho, Pr. Rubens Eduardo Silva"

        # Enviar email apenas em produção, ou silenciar erros em dev
        if settings.DEBUG:
            # Em desenvolvimento, apenas log sem enviar email
            logger.info(f"Email de boas-vindas não enviado em DEBUG para: {user.email}")
        else:
            try:
                send_message("Bem-vindo à Comunidade IBARECISA!", message, [user.email])
            except Exception as e:
                logger.error(f"Erro ao enviar email de boas-vindas: {e}")
                # Não falhar o registro se o email falhar
        return response
