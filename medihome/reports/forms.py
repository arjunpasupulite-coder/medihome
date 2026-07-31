from django import forms
from .models import MedicalReport

class MedicalReportUploadForm(forms.ModelForm):
    class Meta:
        model = MedicalReport
        fields = ['report_title', 'report_type', 'pdf_file', 'summary_notes']
        widgets = {
            'report_title': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'summary_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
