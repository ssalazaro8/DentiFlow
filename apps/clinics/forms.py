from django import forms
from .models import Clinic


class ClinicForm(forms.ModelForm):

    class Meta:

        model = Clinic

        fields = "__all__"