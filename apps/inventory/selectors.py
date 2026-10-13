from .models import Material, MaterialConsumption


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