from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "full_name", "email", "phone", "address",
            "city", "postal_code", "payment_method", "transaction_reference",
        ]
        widgets = {
            "address": forms.TextInput(attrs={"placeholder": "House number, street and area"}),
            "payment_method": forms.RadioSelect(),
            "transaction_reference": forms.TextInput(
                attrs={"placeholder": "Optional UPI transaction reference"}
            ),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("payment_method") == "upi" and not cleaned.get("transaction_reference"):
            self.add_error(
                "transaction_reference",
                "Enter the UPI transaction reference after payment.",
            )
        return cleaned
