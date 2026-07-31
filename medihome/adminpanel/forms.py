from django import forms
from .models import Review
from diagnostics.models import SymptomTestMapping

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['target_type', 'target_id', 'rating', 'comment']
        widgets = {
            'target_type': forms.Select(attrs={'class': 'form-control'}),
            'target_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SymptomTestMappingForm(forms.ModelForm):
    class Meta:
        model = SymptomTestMapping
        fields = ['symptom', 'test_name', 'frequency_weight']
        widgets = {
            'symptom': forms.Select(attrs={'class': 'form-control'}),
            'test_name': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency_weight': forms.Select(attrs={'class': 'form-control'}),
        }
