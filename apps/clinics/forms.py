from django import forms
from .models import Clinic


class ClinicForm(forms.ModelForm):

    class Meta:

        model = Clinic

        # The clinic's accounts are linked from the administration site.
        exclude = ["users"]