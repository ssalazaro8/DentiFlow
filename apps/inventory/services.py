from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.dental_cases.models import DentalCase
from .models import Material, MaterialConsumption, StockAlert
from .selectors import MaterialSelector


class StockAlertService:
    """FR-28: abre y cierra las alertas de stock minimo."""

    @staticmethod
    def sync(material):
        """
        Compara el stock real del material con su nivel minimo.

        - En o bajo el minimo: deja UNA alerta abierta (si ya existe no
          crea otra).
        - Sobre el minimo: cierra la alerta abierta, si la hay.
        """

        # Se vuelve a leer de la base de datos para comparar numeros
        # reales y no el texto que pudo llegar desde un formulario.
        current = Material.objects.get(pk=material.pk)

        if current.stock_quantity <= current.reorder_level:
            alert, _ = StockAlert.objects.get_or_create(
                material=current,
                status=StockAlert.Status.OPEN,
                defaults={
                    "stock_when_opened": current.stock_quantity,
                    "reorder_level_when_opened": current.reorder_level,
                },
            )
            return alert

        StockAlert.objects.filter(
            material=current,
            status=StockAlert.Status.OPEN,
        ).update(
            status=StockAlert.Status.CLOSED,
            closed_at=timezone.now(),
        )
        return None


class MaterialService:

    @staticmethod
    def get_all():
        return MaterialSelector.get_all()

    @staticmethod
    def get_by_id(id):
        return MaterialSelector.get_by_id(id)

    @staticmethod
    def update_stock(material, stock_quantity):
        material.stock_quantity = stock_quantity
        material.save()

        # FR-28: todo movimiento de inventario revisa el stock minimo.
        StockAlertService.sync(material)

        return material

class MaterialConsumptionService:
    """FR-13: registra consumos de material y los descuenta del stock."""

    @staticmethod
    def register(*, dental_case, material, quantity, user):
        quantity = Decimal(quantity)

        if quantity <= 0:
            raise ValueError("The quantity must be greater than zero.")

        if dental_case.status != DentalCase.Status.IN_PROGRESS:
            raise ValueError(
                "Materials can only be recorded while the case is in production."
            )

        with transaction.atomic():
            locked = Material.objects.select_for_update().get(pk=material.pk)

            if quantity > locked.stock_quantity:
                raise ValueError(
                    f"Not enough stock of {locked.name}: "
                    f"{locked.stock_quantity} available, {quantity} requested."
                )

            locked.stock_quantity -= quantity
            locked.save(update_fields=["stock_quantity"])

            # FR-28: el consumo tambien revisa el stock minimo.
            StockAlertService.sync(locked)

            return MaterialConsumption.objects.create(
                dental_case=dental_case,
                material=locked,
                quantity=quantity,
                registered_by=user,
            )