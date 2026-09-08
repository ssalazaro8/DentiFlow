from django.db import models
from django.conf import settings

# Create your models here.

class Laboratory(models.Model):
    # Opciones predefinidas para el tipo de servicio
    SERVICES = [
        ("CROWN", "Dental Crowns"),
        ("BRIDGE", "Dental Bridges"),
        ("IMPLANT", "Dental Implants"),
        ("ORTHODONTICS", "Orthodontics"),
        ("PROSTHESIS", "Dental Prosthesis"),
        ("OTHER", "Other"),
    ]

    # Campos / Columnas de la tabla
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=200)
    service = models.CharField(max_length=20, choices=SERVICES)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Users allowed to receive and manage cases for this laboratory.
    authorized_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="authorized_laboratories",
    )
    # Kept separately because a laboratory user is not necessarily a technician.
    technicians = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="technician_laboratories",
    )

    class Meta:
        ordering = ["name"]  # Ordena automáticamente por nombre

    def __str__(self):
        return self.name  # Cómo se muestra el laboratorio en texto (ej. en el admin)
