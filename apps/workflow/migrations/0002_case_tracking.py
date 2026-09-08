from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def connect_existing_workflows(apps, schema_editor):
    Workflow = apps.get_model("workflow", "Workflow")
    DentalCase = apps.get_model("dental_cases", "DentalCase")
    for workflow in Workflow.objects.filter(dental_case__isnull=True):
        dental_case = DentalCase.objects.filter(case_number=workflow.case_number).first()
        if dental_case:
            workflow.dental_case = dental_case
            workflow.save(update_fields=["dental_case"])


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("dental_cases", "0002_laboratory_acceptance_technician_assignment"),
        ("workflow", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="workflow",
            name="dental_case",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="workflow", to="dental_cases.dentalcase"),
        ),
        migrations.RunPython(connect_existing_workflows, migrations.RunPython.noop),
        migrations.RemoveField(model_name="workflow", name="case_number"),
        migrations.AddField(model_name="workflow", name="progress_percentage", field=models.PositiveSmallIntegerField(default=0)),
        migrations.CreateModel(
            name="WorkflowUpdate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stage", models.CharField(choices=[("RECEIVED", "Received"), ("DESIGN", "3D Design"), ("PRINTING", "Printing / Milling"), ("QC", "Quality Control"), ("SHIPPED", "Shipped")], max_length=20)),
                ("progress_percentage", models.PositiveSmallIntegerField()),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="workflow_updates", to=settings.AUTH_USER_MODEL)),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="updates", to="workflow.workflow")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
