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
                    "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all",
                }
            ),
        }

    def clean_excerpt(self):
        excerpt = self.cleaned_data.get('excerpt', '')
        # TinyMCE returns <p>&nbsp;</p> for empty content
        if excerpt in ['', '<p>&nbsp;</p>', '<p></p>', '<br>', '<p>​</p>', '<p> </p>', '<p><br></p>']:
            return ''
        return excerpt
