from django.db import models
from django.conf import settings
from reports.models import validate_pdf_extension, validate_max_file_size

class TelemedicineConsultation(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telemedicine_consultations')
    doctor = models.ForeignKey('hospitals.Doctor', on_delete=models.CASCADE, related_name='telemedicine_consultations')
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    video_room_id = models.CharField(max_length=100, unique=True)
    consultation_notes = models.TextField(blank=True, null=True)
    prescription_file = models.FileField(
        upload_to='prescriptions/',
        blank=True,
        null=True,
        validators=[validate_pdf_extension, validate_max_file_size],
        help_text="Upload prescription PDF (Max 5MB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_time']

    def __str__(self):
        return f"Consultation with Dr. {self.doctor.name} ({self.get_status_display()})"


class ChatMessage(models.Model):
    consultation = models.ForeignKey(TelemedicineConsultation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M')}] {self.sender.username}: {self.message[:30]}"
