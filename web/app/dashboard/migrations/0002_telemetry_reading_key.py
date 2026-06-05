from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="telemetry",
            name="reading_key",
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
