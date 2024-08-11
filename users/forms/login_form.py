from django.contrib.auth.forms import AuthenticationForm
from users.models import CustomUser


class LoginForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "password")

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields["username"].label = ""
        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["username"].widget.attrs["placeholder"] = "Nome do usuário"
        self.fields["password"].label = ""
        self.fields["password"].widget.attrs["class"] = "form-control"
        self.fields["password"].widget.attrs["placeholder"] = "senha"
