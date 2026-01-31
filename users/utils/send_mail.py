from django.core.mail import send_mail
from django.conf import settings

mail_subject = "Test"
mail_message = "Mensagem..."
from_email = settings.DEFAULT_FROM_EMAIL
send_mail(mail_subject, mail_message, from_email, ["naoresponda@ibarecisa.org.br"])


def send_message(mail_subject="Test",
                  mail_message="Mensagem...",
                  recipient_email="naoresponda@ibarecisa.org.br"):
    send_mail(mail_subject, mail_message,
              settings.DEFAULT_FROM_EMAIL, [recipient_email])
