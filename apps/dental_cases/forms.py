from django import forms
from django.contrib.auth import get_user_model

from .models import DentalCase


class DentalCaseCreateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["laboratory"].required = True
        self.fields["clinic"].required = True

    class Meta:
        model = DentalCase

        fields = [
            "case_number",
            "clinic",
            "requested_by",
            "laboratory",
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
            "clinic": forms.Select(
                attrs={"class": "form-select"}
            ),
            "requested_by": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Dentist requesting the order",
                }
            ),
            "laboratory": forms.Select(
                attrs={"class": "form-select"}
            ),
            "service_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe the requested dental work.",
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


class DentalCaseUpdateForm(forms.ModelForm):

    class Meta:
        model = DentalCase

        fields = [
            "clinic_name",
            "requested_by",
            "service_type",
            "description",
            "observations",
            "due_date",
        ]

        widgets = {
            "clinic_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "requested_by": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "service_type": forms.Select(
                attrs={"class": "form-select"}
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
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }


class RejectionForm(forms.Form):

    reason = forms.CharField(
        label="Reason for rejection",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
            }
        ),
    )


class TechnicianAssignmentForm(forms.Form):

    technician = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        empty_label="Select a technician",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    def __init__(self, *args, laboratory=None, **kwargs):

        super().__init__(*args, **kwargs)

        if laboratory is not None:
            self.fields["technician"].queryset = (
                laboratory.technicians
                .all()
                .order_by("first_name", "last_name", "username")
            )