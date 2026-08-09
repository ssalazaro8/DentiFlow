from .models import Material

from .selectors import MaterialSelector


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

        return material

    