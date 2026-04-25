from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("worship", "0010_songfile_file_title"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WorshipService",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateField(auto_now_add=True, verbose_name="Data de Criação")),
                ("modified", models.DateField(auto_now_add=True, verbose_name="Data de Atualização")),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo?")),
                ("title", models.CharField(max_length=180)),
                (
                    "service_kind",
                    models.CharField(
                        choices=[
                            ("REGULAR", "Culto regular"),
                            ("COMMUNION", "Culto de ceia"),
                            ("CANTATA", "Cantata"),
                            ("SPECIAL", "Culto especial"),
                        ],
                        default="REGULAR",
                        max_length=20,
                    ),
                ),
                ("service_date", models.DateField()),
                ("service_time", models.TimeField(blank=True, null=True)),
                ("leaders_text", models.CharField(blank=True, max_length=255)),
                ("program_html", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="worship_services_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-service_date", "-id"]},
        ),
        migrations.CreateModel(
            name="WorshipServiceSong",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateField(auto_now_add=True, verbose_name="Data de Criação")),
                ("modified", models.DateField(auto_now_add=True, verbose_name="Data de Atualização")),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo?")),
                ("song_snapshot", models.CharField(max_length=255)),
                (
                    "source",
                    models.CharField(
                        choices=[("MANUAL", "Registro manual"), ("IMPORTED", "Importado da programação")],
                        default="MANUAL",
                        max_length=20,
                    ),
                ),
                ("order_ref", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sung_songs",
                        to="worship.worshipservice",
                    ),
                ),
                (
                    "song",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sung_entries",
                        to="worship.song",
                    ),
                ),
            ],
            options={"ordering": ["order_ref", "id"]},
        ),
    ]
