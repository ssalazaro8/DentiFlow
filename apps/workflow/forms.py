from django import forms

from .models import Workflow


class WorkflowForm(forms.ModelForm):

    class Meta:
        model = Workflow
        fields = ["dental_case", "current_stage", "comments", "progress_percentage"]


class WorkflowUpdateForm(forms.Form):
    current_stage = forms.ChoiceField(choices=Workflow.STAGE_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    progress_percentage = forms.IntegerField(min_value=0, max_value=100, widget=forms.NumberInput(attrs={"class": "form-control"}))
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))


class WorkflowStageForm(forms.Form):
    """
    FR-23: alta y edicion de una etapa de produccion.
    """

    name = forms.CharField(
        max_length=60,
        label="Stage name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Quality Control",
            }
        ),
    )

    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Active",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
