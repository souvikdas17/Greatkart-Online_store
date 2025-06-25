from django import forms
from .models import ReviewRating

class Reviewform(forms.ModelForm):
    class Meta:
        Model=ReviewRating
        fields=['subject', 'review', 'rating']