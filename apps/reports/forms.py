from django import forms

from apps.dental_cases.models import DentalCase
from apps.workflow.models import Workflow


class ReportFilterForm(forms.Form):
    """
    Filters available when requesting an operational report.

    Every field is optional: with none of them filled the report
    covers the whole laboratory.
    """

    date_from = forms.DateField(
        required=False,
        label="From",
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    date_to = forms.DateField(
        required=False,
        label="To",
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    status = forms.ChoiceField(
        required=False,
        label="Case status",
        choices=[("", "All statuses")] + list(DentalCase.Status.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    stage = forms.ChoiceField(
        required=False,
        label="Workflow stage",
        choices=[("", "All stages")] + list(Workflow.STAGE_CHOICES),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        cleaned_data = super().clean()

        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from and date_to and date_from > date_to:
            self.add_error(
                "date_to",
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
            key: value
            for key, value in self.cleaned_data.items()
            if value
        }
