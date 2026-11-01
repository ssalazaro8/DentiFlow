from datetime import datetime, time, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.dental_cases.models import DentalCase
from apps.notifications.services import NotificationService
from .models import Material, MaterialConsumption, StockAlert
from .selectors import ConsumptionReportSelector, MaterialSelector


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
            alert, created = StockAlert.objects.get_or_create(
                material=current,
                status=StockAlert.Status.OPEN,
                defaults={
                    "stock_when_opened": current.stock_quantity,
                    "reorder_level_when_opened": current.reorder_level,
                },
            )

            # FR-12: solo una alerta NUEVA genera avisos, no la que ya
            # estaba abierta.
            if created:
                NotificationService.notify_stock_alert(alert)

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


class ConsumptionReportService:
    """
    Calcula el reporte de consumo de materiales:
    consumo semanal, promedio por tipo de servicio y dias estimados
    hasta el nivel de reorden.
    """

    WEEKS = 8
    WINDOW_DAYS = 30

    @staticmethod
    def build(now=None):
        now = now or timezone.now()
        materials = list(Material.objects.all())
        labels = {m.id: f"{m.name} ({m.get_unit_type_display()})" for m in materials}

        weekly = ConsumptionReportService._weekly(now, materials, labels)
        by_service = ConsumptionReportService._by_service_type(materials, labels)
        days = ConsumptionReportService._days_until_reorder(now, materials, labels)

        return {
            **weekly,
            **by_service,
            **days,
            "weeks": ConsumptionReportService.WEEKS,
            "window_days": ConsumptionReportService.WINDOW_DAYS,
            "has_any_consumption": bool(
                ConsumptionReportSelector.material_ids_with_consumption()
            ),
        }

    # --- 1. consumo semanal de cada material ---

    @staticmethod
    def _weekly(now, materials, labels):
        weeks = ConsumptionReportService.WEEKS

        # Las semanas empiezan el lunes; la ultima es la semana en curso.
        today = now.date()
        monday = today - timedelta(days=today.weekday())
        week_starts = [monday - timedelta(weeks=i) for i in range(weeks - 1, -1, -1)]
        since = timezone.make_aware(datetime.combine(week_starts[0], time.min))

        totals = {}
        for row in ConsumptionReportSelector.weekly_totals(since):
            week = row["week"]
            week = week.date() if hasattr(week, "date") else week
            totals[(row["material_id"], week)] = row["total"]

        datasets = []
        rows = []

        for material in materials:
            series = [
                totals.get((material.id, start), Decimal("0"))
                for start in week_starts
            ]

            if any(value > 0 for value in series):
                datasets.append({
                    "label": labels[material.id],
                    "data": [float(value) for value in series],
                })

            rows.append({
                "label": labels[material.id],
                "this_week": series[-1],
                "last_week": series[-2],
                "has_data": any(value > 0 for value in series),
            })

        return {
            "weekly_chart": {
                "labels": [start.strftime("%b %d") for start in week_starts],
                "datasets": datasets,
            },
            "weekly_rows": rows,
        }

    # --- 2. promedio por tipo de servicio ---

    @staticmethod
    def _by_service_type(materials, labels):
        service_names = dict(DentalCase.SERVICE_TYPES)
        material_order = {m.id: index for index, m in enumerate(materials)}

        rows = []
        for item in ConsumptionReportSelector.service_type_totals():
            service = item["dental_case__service_type"]
            average = (item["total"] / item["cases"]).quantize(Decimal("0.01"))
            rows.append({
                "service": service_names.get(service, service),
                "material_id": item["material_id"],
                "material": labels.get(item["material_id"], "Unknown material"),
                "total": item["total"],
                "cases": item["cases"],
                "average": average,
            })

        rows.sort(key=lambda r: (r["service"], material_order.get(r["material_id"], 0)))

        service_labels = sorted({r["service"] for r in rows})
        material_ids = []
        for material in materials:
            if any(r["material_id"] == material.id for r in rows):
                material_ids.append(material.id)

        datasets = []
        for material_id in material_ids:
            values = {
                r["service"]: float(r["average"])
                for r in rows if r["material_id"] == material_id
            }
            datasets.append({
                "label": labels[material_id],
                "data": [values.get(name, 0) for name in service_labels],
            })

        return {
            "service_chart": {"labels": service_labels, "datasets": datasets},
            "service_rows": rows,
        }

    # --- 3. dias hasta el nivel de reorden ---

    @staticmethod
    def _days_until_reorder(now, materials, labels):
        window = ConsumptionReportService.WINDOW_DAYS
        since = now - timedelta(days=window)

        consumed = {
            row["material_id"]: row["total"]
            for row in ConsumptionReportSelector.totals_since(since)
        }
        ever = ConsumptionReportSelector.material_ids_with_consumption()

        rows = []
        chart_labels = []
        chart_data = []

        for material in materials:
            consumed_window = consumed.get(material.id, Decimal("0"))
            available = material.stock_quantity - material.reorder_level

            row = {
                "label": labels[material.id],
                "stock": material.stock_quantity,
                "reorder_level": material.reorder_level,
                "consumed_window": consumed_window,
                "average_daily": None,
                "days": None,
                "status": "ok",
                "message": "",
            }

            if consumed_window <= 0:
                row["status"] = "no_consumption"
                row["message"] = (
                    f"No consumption in the last {window} days."
                    if material.id in ever
                    else "No recorded consumption."
                )
            else:
                row["average_daily"] = (
                    consumed_window / Decimal(window)
                ).quantize(Decimal("0.01"))

                if available <= 0:
                    row["status"] = "at_reorder"
                    row["days"] = Decimal("0.0")
                    row["message"] = "Already at or below the reorder level."
                else:
                    row["days"] = (
                        available / (consumed_window / Decimal(window))
                    ).quantize(Decimal("0.1"))

                chart_labels.append(labels[material.id])
                chart_data.append(float(row["days"]))

            rows.append(row)

        return {
            "days_rows": rows,
            "days_chart": {"labels": chart_labels, "data": chart_data},
            "no_consumption_rows": [r for r in rows if r["status"] == "no_consumption"],
        }