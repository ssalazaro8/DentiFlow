from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from apps.laboratories.models import Laboratory

from .models import LaboratoryUser


class LaboratoryUserForm(forms.ModelForm):

    # FR-16: the account the person signs in with.
    username = forms.CharField(
        max_length=150,
        label="Username",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter username",
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter password",
            }
        ),
    )

    laboratory = forms.ModelChoiceField(
        queryset=Laboratory.objects.all(),
        label="Laboratory",
        empty_label="Select a laboratory",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    def __init__(self, *args, laboratory=None, **kwargs):

        super().__init__(*args, **kwargs)

        # A laboratory administrator registers people in their own
        # laboratory only; the choice is left to superusers.
        if laboratory is not None:
            del self.fields["laboratory"]

    def clean_username(self):

        username = self.cleaned_data["username"]

        if get_user_model().objects.filter(username=username).exists():
            raise forms.ValidationError(
                "An account with this username already exists."
            )

        return username

    def clean_password(self):

        password = self.cleaned_data["password"]

        validate_password(password)

        return password

    class Meta:
        model = LaboratoryUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "status",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter first name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter last name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter email",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter phone number",
                }
            ),
            "role": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }