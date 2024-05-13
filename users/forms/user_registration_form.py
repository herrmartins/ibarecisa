from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser


class RegisterUserForm(UserCreationForm):
    # exemplo de um campo comum, mas o username não dá, nem o password
    """username = forms.CharField(widget=forms.TextInput(
    attrs={"class": "form-control"}))"""

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

        labels = {
            "username": "Nome do usuário:",
            "first_name": "Nome:",
            "last_name": "Sobrenome:",
            "email": "E-mail",
        }

    def __init__(self, *args, **kwargs):
        super(RegisterUserForm, self).__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["username"].widget.attrs[
            "placeholder"
        ] = "Digite o nome do usuário desejado..."

        self.fields["first_name"].widget.attrs["class"] = "form-control"
        self.fields["first_name"].widget.attrs[
            "placeholder"
        ] = "Digite seu primeiro nome..."

        self.fields["email"].widget.attrs["class"] = "form-control"
        self.fields["email"].widget.attrs["placeholder"] = "Digite seu e-mail..."
        self.fields["email"].widget.attrs["type"] = "email"

        self.fields["last_name"].widget.attrs["class"] = "form-control"
        self.fields["last_name"].widget.attrs["placeholder"] = "Digite seu sobrenome..."

        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password1"].widget.attrs["type"] = "password"
        self.fields["password1"].widget.attrs[
            "placeholder"
        ] = "Digite a senha desejada..."

        self.fields["password2"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["type"] = "password"
        self.fields["password2"].widget.attrs[
            "placeholder"
        ] = "Redigite a senha desejada..."
