from django import forms

from .models import DentalCase


class DentalCaseForm(forms.ModelForm):

    class Meta:

        model = DentalCase

        fields = [
            "case_number",
            "clinic_name",
            "requested_by",
            "patient_reference",
            "service_type",
            "description",
            "observations",
        ]