from django import forms

from .models import Workflow


class WorkflowForm(forms.ModelForm):

    class Meta:
        model = Workflow
        fields = "__all__"