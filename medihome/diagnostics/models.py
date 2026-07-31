import math
from django.db import models
from django.conf import settings
from django.db.models import Avg, Count

class DiagnosticianProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diagnostician_profile')
    lab_name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    gst_number = models.CharField(max_length=50)
    nabl_accredited = models.BooleanField(default=False)
    working_hours = models.CharField(max_length=100, default='08:00 AM - 08:00 PM')
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    logo = models.ImageField(upload_to='lab_logos/', blank=True, null=True)
    is_home_collection_available = models.BooleanField(default=True)
    is_approved_by_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lab_name} ({'Approved' if self.is_approved_by_admin else 'Pending Approval'})"

    def get_average_rating(self):
        from adminpanel.models import Review
        avg = Review.objects.filter(target_type='LAB', target_id=self.id).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    def get_total_reviews(self):
        from adminpanel.models import Review
        return Review.objects.filter(target_type='LAB', target_id=self.id).count()

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
            r = 6371  # Radius of Earth in km
            dist = r * c
            return f"{round(dist, 1)} km"
        except Exception:
            return "Distance Not Available"


class DiagnosticTest(models.Model):
    EXCLUDED_HOME_COLLECTION_TESTS = [
        'mri', 'ct scan', 'pet scan', 'ultrasound', 'x-ray', 'xray',
        'endoscopy', 'colonoscopy', 'eeg'
    ]

    lab = models.ForeignKey(DiagnosticianProfile, on_delete=models.CASCADE, related_name='tests')
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, default='General Diagnostics')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    preparation = models.TextField(blank=True, null=True, help_text="e.g. 12 hours fasting required")
    duration_hours = models.PositiveIntegerField(default=24, help_text="Report turnaround time in hours")
    is_home_collection_compatible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Enforce strict domain rule: Incompatible imaging tests can NEVER be marked home collection compatible
        name_lower = self.name.lower()
        if any(excluded in name_lower for excluded in self.EXCLUDED_HOME_COLLECTION_TESTS):
            self.is_home_collection_compatible = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - ₹{self.price} ({self.lab.lab_name})"


class Symptom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class SymptomTestMapping(models.Model):
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE, related_name='test_mappings')
    test_name = models.CharField(max_length=150)
    frequency_weight = models.PositiveIntegerField(default=3, help_text="1 to 5 scale star weight")

    class Meta:
        unique_together = ('symptom', 'test_name')

    def __str__(self):
        return f"{self.symptom.name} -> {self.test_name} ({self.frequency_weight} Stars)"

    def star_display(self):
        return '★' * self.frequency_weight


class Technician(models.Model):
    lab = models.ForeignKey(DiagnosticianProfile, on_delete=models.CASCADE, related_name='technicians')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    area = models.CharField(max_length=150)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.area}) - {'Available' if self.is_available else 'Busy'}"


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    test = models.ForeignKey(DiagnosticTest, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'test')

    def __str__(self):
        return f"{self.test.name} in cart {self.cart.id}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Booking Confirmed'
        TECHNICIAN_ASSIGNED = 'TECHNICIAN_ASSIGNED', 'Technician Assigned'
        TECHNICIAN_ON_THE_WAY = 'TECHNICIAN_ON_THE_WAY', 'Technician On The Way'
        SAMPLE_COLLECTED = 'SAMPLE_COLLECTED', 'Sample Collected'
        REACHED_LABORATORY = 'REACHED_LABORATORY', 'Reached Laboratory'
        TESTING = 'TESTING', 'Testing'
        REPORT_UPLOADED = 'REPORT_UPLOADED', 'Report Uploaded'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    booking_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    diagnostician = models.ForeignKey(DiagnosticianProfile, on_delete=models.CASCADE, related_name='bookings')
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    home_collection_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.CONFIRMED)
    collection_date = models.DateField()
    collection_time = models.CharField(max_length=50)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.booking_number} ({self.get_status_display()})"


class BookingItem(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='items')
    test = models.ForeignKey(DiagnosticTest, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.test.name} (Booking #{self.booking.booking_number})"


class BookingStatusHistory(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=30, choices=Booking.Status.choices)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Booking #{self.booking.booking_number} -> {self.get_status_display()} at {self.timestamp}"
