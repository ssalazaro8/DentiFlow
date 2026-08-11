from django.core.validators import FileExtensionValidator
from django.db import models

from apps.dental_cases.models import DentalCase


def case_file_upload_path(
    instance,
    filename,
):
    return (
        f"case_files/"
        f"{instance.dental_case.case_number}/"
        f"{instance.category}/"
        f"{filename}"
    )


class CaseFile(models.Model):

    class Category(models.TextChoices):

        STL = "STL", "STL File"

        XRAY = "XRAY", "X-Ray"

        PHOTO = "PHOTO", "Photograph"

        PRESCRIPTION = (
            "PRESCRIPTION",
            "Prescription",
        )

        SUPPORTING = (
            "SUPPORTING",
            "Supporting Document",
        )

    dental_case = models.ForeignKey(
        DentalCase,
        on_delete=models.CASCADE,
        related_name="files",
        verbose_name="Dental Case",
    )

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        verbose_name="File Category",
    )

    file = models.FileField(
        upload_to=case_file_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "stl",
                    "jpg",
                    "jpeg",
                    "png",
                    "pdf",
                    "doc",
                    "docx",
                ]
            )
        ],
        verbose_name="File",
    )

    original_name = models.CharField(
        max_length=255,
        verbose_name="Original File Name",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Uploaded At",
    )

    class Meta:

        verbose_name = "Case File"

        verbose_name_plural = "Case Files"

        ordering = [
            "-uploaded_at"
        ]

    def __str__(self):

        return (
            f"{self.dental_case.case_number} - "
            f"{self.original_name}"
        )