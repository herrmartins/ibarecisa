from django.db import migrations, models


def backfill_resolution_status(apps, schema_editor):
    WorshipServiceSong = apps.get_model("worship", "WorshipServiceSong")
    WorshipServiceSong.objects.filter(song__isnull=False).update(resolution_status="LINKED", match_confidence=1)
    WorshipServiceSong.objects.filter(song__isnull=True).update(resolution_status="PENDING_REVIEW")
    WorshipServiceSong.objects.filter(song__isnull=True, song_snapshot__icontains="HA").update(
        resolution_status="UNLINKED",
        resolution_note="Origem detectada como hino avulso.",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("worship", "0013_worshipservice_leader_dirigente_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="song",
            name="hymn_number",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="HymnalAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alias", models.CharField(max_length=80, unique=True)),
                (
                    "hymnal",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="aliases", to="worship.hymnal"),
                ),
            ],
            options={
                "ordering": ["alias"],
            },
        ),
        migrations.AddField(
            model_name="worshipservicesong",
            name="detected_hymnal",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="detected_in_service_songs", to="worship.hymnal"),
        ),
        migrations.AddField(
            model_name="worshipservicesong",
            name="detected_hymnal_raw",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="worshipservicesong",
            name="detected_number",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="worshipservicesong",
            name="match_confidence",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name="worshipservicesong",
            name="resolution_note",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="worshipservicesong",
            name="resolution_status",
            field=models.CharField(
                choices=[("LINKED", "Vinculada"), ("PENDING_REVIEW", "Pendente"), ("UNLINKED", "Avulsa")],
                default="PENDING_REVIEW",
                max_length=20,
            ),
        ),
        migrations.RunPython(backfill_resolution_status, migrations.RunPython.noop),
    ]
