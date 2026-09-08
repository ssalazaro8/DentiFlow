from django.shortcuts import get_object_or_404
from .models import DentalCaseFile


def get_case_file_by_id(*, file_id: int) -> DentalCaseFile:
    return get_object_or_404(DentalCaseFile, id=file_id)