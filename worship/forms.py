from django import forms

from worship.models import Song, WorshipService, WorshipServiceSong
from worship.models import Composer, Hymnal, SongTheme


class WorshipServiceForm(forms.ModelForm):
    class Meta:
        model = WorshipService
        fields = [
            "title",
            "service_kind",
            "service_date",
            "service_time",
            "leader_dirigente",
            "leader_regente",
            "leader_musician",
            "program_html",
            "notes",
        ]
        widgets = {
            "service_date": forms.DateInput(attrs={"type": "date", "class": "app-input w-full"}),
            "service_time": forms.TimeInput(attrs={"type": "time", "class": "app-input w-full"}),
            "title": forms.TextInput(attrs={"class": "app-input w-full"}),
            "service_kind": forms.Select(attrs={"class": "app-input w-full"}),
            "leader_dirigente": forms.TextInput(attrs={"class": "app-input w-full", "placeholder": "Ex: Breno"}),
            "leader_regente": forms.TextInput(attrs={"class": "app-input w-full", "placeholder": "Ex: Jhonathan"}),
            "leader_musician": forms.TextInput(attrs={"class": "app-input w-full", "placeholder": "Ex: Mellyne"}),
            "program_html": forms.Textarea(attrs={"class": "app-input w-full", "rows": 14, "id": "id_program_html"}),
            "notes": forms.Textarea(attrs={"class": "app-input w-full", "rows": 4}),
        }


class WorshipServiceSongForm(forms.ModelForm):
    class Meta:
        model = WorshipServiceSong
        fields = ["song_snapshot"]
        labels = {
            "song_snapshot": "Canção extra",
        }
        help_texts = {
            "song_snapshot": "Ex: VM 123 - Vencendo vem Jesus",
        }
        widgets = {
            "song_snapshot": forms.TextInput(attrs={"class": "app-input", "placeholder": "Ex: VM 123 - Vencendo vem Jesus"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WorshipServiceImportForm(forms.Form):
    raw_text = forms.CharField(
        label="Texto base da programação",
        widget=forms.Textarea(attrs={"class": "app-input", "rows": 14}),
    )
    model_hint = forms.CharField(
        label="Instrução extra (opcional)",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "app-input",
                "placeholder": "Ex: manter estilo tradicional, incluir campo de ceia quando houver",
            }
        ),
    )


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = [
            "title",
            "artist",
            "themes",
            "hymnal",
            "hymn_number",
            "key",
            "metrics",
            "lyrics",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "app-input w-full", "placeholder": "Ex: Vencendo vem Jesus"}),
            "artist": forms.Select(attrs={"class": "app-input w-full"}),
            "themes": forms.SelectMultiple(attrs={"class": "app-input w-full", "size": 6}),
            "hymnal": forms.Select(attrs={"class": "app-input w-full"}),
            "hymn_number": forms.NumberInput(attrs={"class": "app-input w-full", "min": 1, "placeholder": "Ex: 123"}),
            "key": forms.Select(attrs={"class": "app-input w-full"}),
            "metrics": forms.TextInput(attrs={"class": "app-input w-full", "placeholder": "Ex: 8.7.8.7"}),
            "lyrics": forms.Textarea(attrs={"class": "app-input w-full", "rows": 14, "id": "id_lyrics"}),
        }
        labels = {
            "artist": "Compositor",
            "themes": "Temas",
            "hymnal": "Hinário",
            "hymn_number": "Número do hino",
            "key": "Tom",
            "metrics": "Métrica",
            "lyrics": "Letra",
        }


class ComposerQuickForm(forms.ModelForm):
    class Meta:
        model = Composer
        fields = ["name", "bio"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "app-input w-full", "placeholder": "Ex: Charles Wesley"}),
            "bio": forms.Textarea(attrs={"class": "app-input w-full", "rows": 3, "placeholder": "Opcional"}),
        }
        labels = {
            "name": "Nome",
            "bio": "Bio",
        }


class HymnalQuickForm(forms.ModelForm):
    class Meta:
        model = Hymnal
        fields = ["title", "author", "edition"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "app-input w-full", "placeholder": "Ex: Hinário Para o Culto Cristão"}),
            "author": forms.TextInput(attrs={"class": "app-input w-full", "placeholder": "Opcional"}),
            "edition": forms.NumberInput(attrs={"class": "app-input w-full", "min": 1, "placeholder": "Opcional"}),
        }
        labels = {
            "title": "Título",
            "author": "Autor",
            "edition": "Edição",
        }


class SongThemeQuickForm(forms.ModelForm):
    class Meta:
        model = SongTheme
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "app-input w-full", "placeholder": "Ex: Natal"}),
        }
        labels = {
            "title": "Tema",
        }
