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
