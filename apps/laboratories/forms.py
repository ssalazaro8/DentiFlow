from django import forms
from django.contrib.auth import get_user_model
from .models import Laboratory


class LaboratoryForm(forms.ModelForm):
    class Meta:
        model = Laboratory
        fields = [
            "name", "email", "phone", "city", "address", "service",
            "rating", "is_active",
        ]


class TechnicianCreateForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))

    def clean_username(self):
        username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username=username).exists():
            raise forms.ValidationError("A technician with this username already exists.")
        return username
