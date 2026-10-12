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


class DentalCaseFilterForm(forms.Form):
    """
    Search term and filters of the dental case list.

    Every field is optional: with none of them filled the list shows
    every case the user is allowed to see.
    """

    q = forms.CharField(
        required=False,
        max_length=150,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Case number, clinic or requester",
            }
        ),
    )

    status = forms.ChoiceField(
        required=False,
        label="Status",
        choices=[("", "All statuses")] + list(DentalCase.Status.choices),
        widget=forms.Select(
            attrs={"class": "form-select"}
        ),
    )

    service_type = forms.ChoiceField(
        required=False,
        label="Service",
        choices=[("", "All services")] + list(DentalCase.SERVICE_TYPES),
        widget=forms.Select(
            attrs={"class": "form-select"}
        ),
    )

    due_from = forms.DateField(
        required=False,
        label="Due from",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )

    due_to = forms.DateField(
        required=False,
        label="Due to",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )

    def clean(self):

        cleaned_data = super().clean()

        due_from = cleaned_data.get("due_from")
        due_to = cleaned_data.get("due_to")

        if due_from and due_to and due_from > due_to:
            self.add_error(
                "due_to",
                "The end date cannot be earlier than the start date.",
            )

        return cleaned_data

    def as_filters(self):
        """
        Returns the cleaned filters, dropping the empty ones.
        """

        if not self.is_valid():
            return {}

        return {
            name: value
            for name, value in self.cleaned_data.items()
            if value
        }

    def applied_filters(self):
        """
        Returns the applied filters with a readable value, for display.
        """

        applied = []

        for name, value in self.as_filters().items():

            field = self.fields[name]

            if isinstance(field, forms.ChoiceField):
                value = dict(field.choices).get(value, value)

            applied.append(
                {
                    "label": field.label,
                    "value": value,
                }
            )

        return applied
