from django.db import models
from core.models import BaseModel
from ckeditor.fields import RichTextField
from worship.models.worship_utils import count_syllables_portuguese
from bs4 import BeautifulSoup


class Song(models.Model):
    MUSICAL_KEYS = [
        ("C", "C"),
        ("C#", "C#"),
        ("Db", "Db"),
        ("D", "D"),
        ("D#", "D#"),
        ("Eb", "Eb"),
        ("E", "E"),
        ("F", "F"),
        ("F#", "F#"),
        ("Gb", "Gb"),
        ("G", "G"),
        ("G#", "G#"),
        ("Ab", "Ab"),
        ("A", "A"),
        ("A#", "A#"),
        ("Bb", "Bb"),
        ("B", "B"),
    ]

    title = models.CharField(max_length=200)
    artist = models.ForeignKey(
        "Composer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="songs",
    )
    key = models.CharField(max_length=2, choices=MUSICAL_KEYS, blank=True, null=True)
    lyrics = RichTextField(blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    themes = models.ManyToManyField("SongTheme", related_name="songs", blank=True)
    hymnal = models.ForeignKey(
        "Hymnal",
        related_name="hymnal_songs",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    syllable_counts_json = models.JSONField(default=dict)

    def save(self, *args, **kwargs):
        self.syllable_counts_json = self.calculate_syllables()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def syllable_counts(self):
        return self.syllable_counts_json

    @staticmethod
    def count_syllables_in_line(line):
        """
        Count the number of syllables in a line of text.
        """
        return count_syllables_portuguese(line)

    def calculate_syllables(self):
        """
        Calculate the syllable counts for each line in the lyrics.
        """
        if not self.lyrics:
            return {}

        soup = BeautifulSoup(self.lyrics, "html.parser")
        text = soup.get_text()
        lines = text.splitlines()
        syllable_counts = {line: self.count_syllables_in_line(line) for line in lines}
        return syllable_counts
