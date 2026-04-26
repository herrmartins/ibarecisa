from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("worship", "0011_worship_service_program_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="worshipservice",
            name="program_font_scale",
            field=models.PositiveSmallIntegerField(default=100),
        ),
    ]
