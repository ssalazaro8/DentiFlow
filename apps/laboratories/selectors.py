from .models import Laboratory


class LaboratorySelector:

    @staticmethod
    def get_all():
        # Devuelve solo los laboratorios que estén activos
        return Laboratory.objects.filter(is_active=True)

    @staticmethod
    def search(city=None, service=None):
        # Empieza filtrando los activos
        queryset = Laboratory.objects.filter(is_active=True)

        # Si el usuario escribió una ciudad, filtra ignorando mayúsculas/minúsculas (icontains)
        if city:
            queryset = queryset.filter(city__icontains=city)

        # Si el usuario seleccionó un servicio, filtra por ese servicio exacto
        if service:
            queryset = queryset.filter(service=service)

        return queryset