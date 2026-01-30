from django import forms
from secretarial.models import MinuteExcerptsModel


class MinuteExcerptsModelForm(forms.ModelForm):
    excerpt = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = MinuteExcerptsModel
        fields = ['title', 'excerpt']

        labels = {
            "title": "Título",
            "excerpt": "Trecho",
        }

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-input",
                }
            ),
        }

    def clean_excerpt(self):
        excerpt = self.cleaned_data.get('excerpt', '')
        # Quill returns <p><br></p> for empty content
        if excerpt in ['', '<p><br></p>', '<p></p>', '<br>', '<p>​</p>', '<p> </p>']:
            return ''
        return excerpt
