from .models import Material


class MaterialSelector:

    @staticmethod
    def get_all():
        return Material.objects.all()

    @staticmethod
    def get_by_id(id):
        return Material.objects.get(id=id)