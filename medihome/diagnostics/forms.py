from django import forms
from .models import DiagnosticTest, Technician

class DiagnosticTestForm(forms.ModelForm):
    class Meta:
        model = DiagnosticTest
        fields = ['name', 'category', 'price', 'preparation', 'duration_hours', 'is_home_collection_compatible']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Complete Blood Count (CBC)'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Hematology / General'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price in ₹'}),
            'preparation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Preparation guidelines'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_home_collection_compatible': forms.CheckboxInput(),
        }

class TechnicianForm(forms.ModelForm):
    class Meta:
        model = Technician
        fields = ['name', 'phone', 'area', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Technician Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Coverage Zone / Area'}),
            'is_available': forms.CheckboxInput(),
        }
