from django.db import models

from core.models import BaseModel
from users.models import CustomUser


class WorshipService(BaseModel):
    KIND_REGULAR = "REGULAR"
    KIND_COMMUNION = "COMMUNION"
    KIND_CANTATA = "CANTATA"
    KIND_SPECIAL = "SPECIAL"

    KIND_CHOICES = [
        (KIND_REGULAR, "Culto regular"),
        (KIND_COMMUNION, "Culto de ceia"),
        (KIND_CANTATA, "Cantata"),
        (KIND_SPECIAL, "Culto especial"),
    ]

    title = models.CharField(max_length=180, verbose_name="Título")
    service_kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_REGULAR, verbose_name="Tipo de culto")
    service_date = models.DateField(verbose_name="Data")
    service_time = models.TimeField(blank=True, null=True, verbose_name="Horário")
    leaders_text = models.CharField(max_length=255, blank=True, verbose_name="Liderança")
    leader_dirigente = models.CharField(max_length=100, blank=True, verbose_name="Dirigente")
    leader_regente = models.CharField(max_length=100, blank=True, verbose_name="Regente")
    leader_musician = models.CharField(max_length=100, blank=True, verbose_name="Pianista/Músico")
    program_font_scale = models.PositiveSmallIntegerField(default=100, verbose_name="Escala da fonte")
    program_html = models.TextField(blank=True, verbose_name="Programação")
    notes = models.TextField(blank=True, verbose_name="Observações")
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="worship_services_created",
    )

    class Meta:
        ordering = ["-service_date", "-id"]

    def __str__(self):
        return f"{self.title} - {self.service_date:%d/%m/%Y}"


class WorshipServiceSong(BaseModel):
    SOURCE_MANUAL = "MANUAL"
    SOURCE_IMPORTED = "IMPORTED"

    SOURCE_CHOICES = [
        (SOURCE_MANUAL, "Registro manual"),
        (SOURCE_IMPORTED, "Importado da programação"),
    ]

    RESOLUTION_LINKED = "LINKED"
    RESOLUTION_PENDING_REVIEW = "PENDING_REVIEW"
    RESOLUTION_UNLINKED = "UNLINKED"

    RESOLUTION_CHOICES = [
        (RESOLUTION_LINKED, "Vinculada"),
        (RESOLUTION_PENDING_REVIEW, "Pendente"),
        (RESOLUTION_UNLINKED, "Avulsa"),
    ]

    service = models.ForeignKey(
        WorshipService,
        on_delete=models.CASCADE,
        related_name="sung_songs",
    )
    song = models.ForeignKey(
        "worship.Song",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sung_entries",
    )
    song_snapshot = models.CharField(max_length=255)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    order_ref = models.PositiveIntegerField(blank=True, null=True)
    resolution_status = models.CharField(
        max_length=20,
        choices=RESOLUTION_CHOICES,
        default=RESOLUTION_PENDING_REVIEW,
    )
    detected_hymnal_raw = models.CharField(max_length=80, blank=True)
    detected_hymnal = models.ForeignKey(
        "worship.Hymnal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detected_in_service_songs",
    )
    detected_number = models.PositiveIntegerField(null=True, blank=True)
    match_confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    resolution_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["order_ref", "id"]

    def __str__(self):
        return self.song_snapshot
