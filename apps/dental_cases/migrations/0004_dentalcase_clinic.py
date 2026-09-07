from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clinics", "0001_initial"),
        ("dental_cases", "0003_dentalcase_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="dentalcase",
            name="clinic",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="dental_cases",
                to="clinics.clinic",
            ),
        ),
    ]
