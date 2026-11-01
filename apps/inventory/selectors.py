from django.db.models import Count, Sum
from django.db.models.functions import TruncWeek

from .models import Material, MaterialConsumption, StockAlert


class MaterialSelector:

    @staticmethod
    def get_all():
        return Material.objects.all()

    @staticmethod
    def get_by_id(id):
        return Material.objects.get(id=id)

class MaterialConsumptionSelector:

    @staticmethod
    def for_case(dental_case):
        return (
            MaterialConsumption.objects
            .filter(dental_case=dental_case)
            .select_related("material", "registered_by")
        )

class StockAlertSelector:

    @staticmethod
    def open_alerts():
        return (
            StockAlert.objects
            .filter(status=StockAlert.Status.OPEN)
            .select_related("material")
        )


class ConsumptionReportSelector:
    """Lecturas agregadas para el reporte de consumo de materiales."""

    @staticmethod
    def weekly_totals(since):
        """Cantidad consumida por material y por semana desde `since`."""

        return list(
            MaterialConsumption.objects
            .filter(consumed_at__gte=since)
            .annotate(week=TruncWeek("consumed_at"))
            .order_by()
            .values("material_id", "week")
            .annotate(total=Sum("quantity"))
        )

    @staticmethod
    def totals_since(since):
        """Cantidad total consumida por material desde `since`."""

        return list(
            MaterialConsumption.objects
            .filter(consumed_at__gte=since)
            .order_by()
            .values("material_id")
            .annotate(total=Sum("quantity"))
        )

    @staticmethod
    def service_type_totals():
        """Cantidad consumida y casos distintos por material y tipo de servicio."""

        return list(
            MaterialConsumption.objects
            .order_by()
            .values("material_id", "dental_case__service_type")
            .annotate(
                total=Sum("quantity"),
                cases=Count("dental_case", distinct=True),
            )
        )

    @staticmethod
    def material_ids_with_consumption():
        return set(
            MaterialConsumption.objects
            .order_by()
            .values_list("material_id", flat=True)
            .distinct()
        )