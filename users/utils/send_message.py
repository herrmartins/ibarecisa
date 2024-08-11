from django.core.mail import send_mail


def send_message(
    mail_subject="Test",
    mail_message="Mensagem de teste...",
    recipient_email=["rafael@rdmartins.adv.br"],
):
    send_mail(mail_subject, mail_message, "jusrafaelmartin@gmail.com", recipient_email)
