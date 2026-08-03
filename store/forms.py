from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} star" if i == 1 else f"{i} stars") for i in range(5, 0, -1)]),
            "title": forms.TextInput(attrs={"placeholder": "Review title"}),
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Share your experience"}),
        }
