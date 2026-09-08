from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("dental_cases", "0002_laboratory_acceptance_technician_assignment"),
    ]

    operations = [
        migrations.AddField(
            model_name="dentalcase",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="submitted_dental_cases",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
