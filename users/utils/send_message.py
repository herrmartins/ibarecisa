from django.core.mail import send_mail


def send_message(mail_subject="Test",
                 mail_message="Mensagem de teste...",
                 recipient_email=["naoresponda@ibarecisa.org.br"]):
    send_mail(mail_subject, mail_message,
              "naoresponda@ibarecisa.org.br", recipient_email)
