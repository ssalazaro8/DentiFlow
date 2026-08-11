from django import forms

from .models import DentalCase


class DentalCaseCreateForm(forms.ModelForm):

    class Meta:
        model = DentalCase

        fields = [
            "case_number",
            "clinic_name",
            "requested_by",
            "service_type",
            "description",
            "observations",
            "due_date",
        ]

        widgets = {
            "case_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: DF-0001",
                }
            ),
            "clinic_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Dental clinic or office",
                }
            ),
            "requested_by": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Dentist requesting the order",
                }
            ),
            "service_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Describe the requested dental work."
                    ),
                }
            ),
            "observations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Additional observations."
                    ),
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }


class DentalCaseUpdateForm(forms.ModelForm):

    class Meta:
        model = DentalCase

        fields = [
            "clinic_name",
            "requested_by",
            "service_type",
            "description",
            "observations",
            "status",
            "due_date",
        ]

        widgets = {
            "clinic_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "requested_by": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "service_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
            "observations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }