from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from users.models import CustomUser


class ChangeUserPasswordForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'type': 'password',
               'placeholder': 'Digite sua senha antiga...'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'type': 'password',
               'placeholder': "Digite sua nova senha..."}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'type': 'password',
               'placeholder': 'Confirme sua nova senha...'}))

    class Meta:
        model = CustomUser
        fields = (
            "old_password",
            "new_password1",
            "new_password2",
        )

        labels = {
            "old_password": "Senha antiga",
            "new_password1": "",
            "new_password2": "",
        }

    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Senha antiga'
        self.fields['new_password1'].label = 'Nova senha'
        self.fields['new_password2'].label = 'Confirme a senha'