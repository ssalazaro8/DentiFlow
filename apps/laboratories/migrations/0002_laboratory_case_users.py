from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("laboratories", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="laboratory",
            name="authorized_users",
            field=models.ManyToManyField(blank=True, related_name="authorized_laboratories", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="laboratory",
            name="technicians",
            field=models.ManyToManyField(blank=True, related_name="technician_laboratories", to=settings.AUTH_USER_MODEL),
        ),
    ]
