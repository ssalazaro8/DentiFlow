from .models import Laboratory
from .selectors import LaboratorySelector


class LaboratoryService:

    @staticmethod
    def get_all():
        # Llama al selector para obtener todos
        return LaboratorySelector.get_all()

    @staticmethod
    def search(city=None, service=None, min_rating=None):
        # Llama al selector para buscar
        return LaboratorySelector.search(city=city, service=service, min_rating=min_rating)

    @staticmethod
    def create(data):
        # Toma el diccionario de datos validados y crea un nuevo registro en la BD
        return Laboratory.objects.create(**data)