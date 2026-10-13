from django import forms

from .models import Material


class MaterialChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.name} ({obj.stock_quantity} {obj.get_unit_type_display()} available)"


class MaterialConsumptionForm(forms.Form):
    material = MaterialChoiceField(
        queryset=Material.objects.all(),
        empty_label="Select a material",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    quantity = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.01", "placeholder": "Quantity"}
        ),
    )