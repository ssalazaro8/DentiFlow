from django import forms
from .models import Laboratory


class LaboratoryForm(forms.ModelForm):
    class Meta:
        model = Laboratory
        fields = "__all__"  # Incluye todos los campos del modelo en el formulario