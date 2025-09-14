from decouple import config
from django.core.mail import send_mail

mail_subject = "Test"
mail_message = "Mensagem..."
from_email = "jusrafaelmartin@gmail.com"
send_mail(mail_subject, mail_message, from_email, ["rafael@rdmartins.adv.br"])


def send_message(mail_subject="Test",
                  mail_message="Mensagem...",
                  recipient_email="rafael@rdmartins.adv.br"):
    send_mail(mail_subject, mail_message,
              "jusrafaelmartin@gmail.com", [recipient_email])
