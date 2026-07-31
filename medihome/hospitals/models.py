import math
from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.db.models import Avg, Count

class HospitalProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hospital_profile')
    hospital_name = models.CharField(max_length=150)
    license_number = models.CharField(max_length=50)
    gst_number = models.CharField(max_length=50)
    emergency_contact = models.CharField(max_length=20)
    working_hours = models.CharField(max_length=100, default='24/7 Emergency & OPD 09:00 AM - 08:00 PM')
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    logo = models.ImageField(upload_to='hospital_logos/', blank=True, null=True)
    is_approved_by_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hospital_name} ({'Approved' if self.is_approved_by_admin else 'Pending Approval'})"

    def get_average_rating(self):
        from adminpanel.models import Review
        avg = Review.objects.filter(target_type='HOSPITAL', target_id=self.id).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    def get_total_reviews(self):
        from adminpanel.models import Review
        return Review.objects.filter(target_type='HOSPITAL', target_id=self.id).count()

    def calculate_distance(self, user_lat, user_lng):
        if not self.latitude or not self.longitude or user_lat is None or user_lng is None:
            return "Distance Not Available"
        try:
            lat1, lon1 = math.radians(float(user_lat)), math.radians(float(user_lng))
            lat2, lon2 = math.radians(float(self.latitude)), math.radians(float(self.longitude))
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            r = 6371
            dist = r * c
            return f"{round(dist, 1)} km"
        except Exception:
            return "Distance Not Available"


class Department(models.Model):
    STANDARD_DEPARTMENTS = [
        'General Medicine', 'Cardiology', 'Neurology', 'ENT',
        'Orthopedics', 'Gynecology', 'Pediatrics', 'Dental', 'Dermatology'
    ]

    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('hospital', 'name')

    def __str__(self):
        return f"{self.name} ({self.hospital.hospital_name})"


class Doctor(models.Model):
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name='doctors')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=100)
    qualification = models.CharField(max_length=150, help_text="e.g. MBBS, MD (Cardiology)")
    specialization = models.CharField(max_length=100)
    experience_years = models.PositiveIntegerField(default=5)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2)
    available_days = models.CharField(max_length=100, default='Mon, Tue, Wed, Thu, Fri, Sat')
    available_time_start = models.TimeField(default='09:00:00')
    available_time_end = models.TimeField(default='17:00:00')
    photo = models.ImageField(upload_to='doctor_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.name} - {self.specialization} ({self.hospital.hospital_name})"

    def get_average_rating(self):
        from adminpanel.models import Review
        avg = Review.objects.filter(target_type='DOCTOR', target_id=self.id).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    def get_available_slots(self, target_date=None):
        """Automatically generates 30-minute available time slots based on working hours"""
        slots = []
        try:
            curr = datetime.combine(datetime.today(), self.available_time_start)
            end = datetime.combine(datetime.today(), self.available_time_end)
            slot_duration = timedelta(minutes=30)
            
            while curr + slot_duration <= end:
                slot_str = curr.strftime("%I:%M %p")
                slots.append(slot_str)
                curr += slot_duration
        except Exception:
            slots = ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"]
        return slots


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        REFUNDED = 'REFUNDED', 'Refunded'

    appointment_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.CharField(max_length=30)
    symptom_reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PAID)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-appointment_date', '-created_at']

    def __str__(self):
        return f"OP Appointment #{self.appointment_number} with Dr. {self.doctor.name}"
