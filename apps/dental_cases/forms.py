from django import forms

from .models import DentalCase


class DentalCaseBaseForm(forms.ModelForm):
    """
    Shared fields and widgets for dental case forms.
    """

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
                    "placeholder": "Additional observations.",
                }
            ),

            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

        labels = {
            "case_number": "Case Number",
            "clinic_name": "Clinic",
            "requested_by": "Requested By",
            "service_type": "Service Type",
            "description": "Description",
            "observations": "Observations",
            "due_date": "Due Date",
        }


class DentalCaseCreateForm(DentalCaseBaseForm):
    """
    Form used to create a new dental case.

    New cases always start as SUBMITTED.
    """

    pass


class DentalCaseUpdateForm(DentalCaseBaseForm):
    """
    Form used to update an existing dental case.
    """

    status = forms.ChoiceField(
        choices=DentalCase.Status.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
        label="Status",
    )

    class Meta(DentalCaseBaseForm.Meta):
        fields = [
            "case_number",
            "clinic_name",
            "requested_by",
            "service_type",
            "description",
            "observations",
            "status",
            "due_date",
        ]