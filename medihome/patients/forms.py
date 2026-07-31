from django import forms
from .models import PatientProfile, MedicineReminder

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['blood_group', 'dob', 'gender', 'emergency_contact', 'medical_history']
        widgets = {
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MedicineReminderForm(forms.ModelForm):
    class Meta:
        model = MedicineReminder
        fields = ['medicine_name', 'morning', 'afternoon', 'night', 'duration_days', 'start_date', 'notes']
        widgets = {
            'medicine_name': forms.TextInput(attrs={'class': 'form-control'}),
            'morning': forms.CheckboxInput(),
            'afternoon': forms.CheckboxInput(),
            'night': forms.CheckboxInput(),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }
