from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("laboratories", "0002_laboratory_case_users"),
        ("dental_cases", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dentalcase",
            name="acceptance_status",
            field=models.CharField(choices=[("PENDING", "Pending laboratory decision"), ("ACCEPTED", "Accepted"), ("REJECTED", "Rejected")], default="PENDING", max_length=12, verbose_name="Laboratory decision"),
        ),
        migrations.AddField(model_name="dentalcase", name="accepted_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(
            model_name="dentalcase",
            name="laboratory",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="dental_cases", to="laboratories.laboratory", verbose_name="Destination laboratory"),
        ),
        migrations.AddField(model_name="dentalcase", name="rejected_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="dentalcase", name="rejection_reason", field=models.TextField(blank=True)),
        migrations.AlterField(
            model_name="dentalcase",
            name="status",
            field=models.CharField(choices=[("SUBMITTED", "Submitted"), ("IN_REVIEW", "In Review"), ("IN_PROGRESS", "In Progress"), ("COMPLETED", "Completed"), ("DELIVERED", "Delivered"), ("CANCELLED", "Cancelled"), ("REJECTED", "Rejected")], default="SUBMITTED", max_length=20, verbose_name="Status"),
        ),
        migrations.CreateModel(
            name="TechnicianAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("dental_case", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="technician_assignment", to="dental_cases.dentalcase")),
                ("technician", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="technician_assignments", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
