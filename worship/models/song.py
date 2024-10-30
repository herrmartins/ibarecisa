from django.db import models
from core.models import BaseModel


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
    lyrics = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    themes = models.ManyToManyField("SongTheme", related_name="songs", blank=True)
    hymnal = models.ForeignKey(
        "Hymnal",
        related_name="hymnal_songs",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.title
