from django import forms
from .models import TelemedicineConsultation, ChatMessage

class PrescriptionUploadForm(forms.ModelForm):
    class Meta:
        model = TelemedicineConsultation
        fields = ['consultation_notes', 'prescription_file']
        widgets = {
            'consultation_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prescription_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['message']
        widgets = {
            'message': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type message...'}),
        }
