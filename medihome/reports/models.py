import os
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

def validate_pdf_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension. Only PDF files (.pdf) are allowed.')

def validate_max_file_size(value):
    max_size_bytes = 5 * 1024 * 1024  # 5 Megabytes
    if value.size > max_size_bytes:
        raise ValidationError(f'File size exceeds maximum allowed threshold of 5MB. Current size is {round(value.size / (1024*1024), 2)}MB.')


class MedicalReport(models.Model):
    REPORT_TYPES = [
        ('BLOOD', 'Blood Test Report'),
        ('URINE', 'Urine Test Report'),
        ('BIOCHEMISTRY', 'Biochemistry Report'),
        ('HAEMATOLOGY', 'Haematology Report'),
        ('OTHER', 'General Health Report'),
    ]

    booking = models.ForeignKey('diagnostics.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_reports')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medical_reports')
    diagnostician = models.ForeignKey('diagnostics.DiagnosticianProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_reports')
    
    report_title = models.CharField(max_length=150)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES, default='BLOOD')
    pdf_file = models.FileField(
        upload_to='medical_reports/',
        validators=[validate_pdf_extension, validate_max_file_size],
        help_text="Only PDF files up to 5MB allowed"
    )
    summary_notes = models.TextField(blank=True, null=True)
    is_hard_copy_requested = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_title} - Patient: {self.patient.username}"
