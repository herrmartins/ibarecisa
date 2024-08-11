from django import forms
from blog.models import Comment
from ckeditor.widgets import CKEditorWidget


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": CKEditorWidget(),
        }
