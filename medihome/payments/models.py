from django.db import models
from django.conf import settings
from django.utils import timezone

class SystemSettings(models.Model):
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=18.00, help_text="GST percentage e.g. 18.0")
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, default=50.00, help_text="Fixed Platform Fee in ₹")
    home_collection_charge = models.DecimalField(max_digits=8, decimal_places=2, default=150.00, help_text="Home sample collection fee in ₹")
    support_email = models.EmailField(default="support@medihome.com")
    support_phone = models.CharField(max_length=20, default="+91 1800-123-4567")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def save(self, *args, **kwargs):
        # Enforce singleton pattern (id=1)
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"MediHome Configuration (GST: {self.gst_percentage}%, Fee: ₹{self.platform_fee})"


class Payment(models.Model):
    class BookingType(models.TextChoices):
        DIAGNOSTIC = 'DIAGNOSTIC', 'Diagnostic Booking'
        HOSPITAL_OP = 'HOSPITAL_OP', 'Hospital OP Booking'

    class PaymentMethod(models.TextChoices):
        UPI = 'UPI', 'UPI Payment'
        CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
        DEBIT_CARD = 'DEBIT_CARD', 'Debit Card'
        NET_BANKING = 'NET_BANKING', 'Net Banking'
        CASH_ON_COLLECTION = 'CASH_ON_COLLECTION', 'Cash on Collection'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    booking_type = models.CharField(max_length=20, choices=BookingType.choices)
    reference_id = models.CharField(max_length=50, help_text="Booking Number or Appointment Number")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUCCESS)
    transaction_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.transaction_id} - ₹{self.amount} ({self.get_status_display()})"


class Invoice(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    line_items_json = models.TextField(help_text="JSON payload summarizing calculated line items")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.invoice_number} for Payment {self.payment.transaction_id}"


class Coupon(models.Model):
    code = models.CharField(max_length=30, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="e.g. 15.0 for 15%")
    discount_max_amount = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    min_order_amount = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    valid_until = models.DateField()
    is_active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(default=100)
    used_count = models.PositiveIntegerField(default=0)

    def is_valid(self, cart_total):
        if not self.is_active:
            return False, "Coupon is inactive."
        if self.valid_until < timezone.now().date():
            return False, "Coupon has expired."
        if self.used_count >= self.usage_limit:
            return False, "Coupon usage limit reached."
        if float(cart_total) < float(self.min_order_amount):
            return False, f"Minimum order amount ₹{self.min_order_amount} required for this coupon."
        return True, "Coupon applied successfully."

    def calculate_discount(self, cart_total):
        val, msg = self.is_valid(cart_total)
        if not val:
            return 0.0
        disc = (float(cart_total) * float(self.discount_percent)) / 100.0
        return min(disc, float(self.discount_max_amount))

    def __str__(self):
        return f"Coupon {self.code} ({self.discount_percent}% OFF up to ₹{self.discount_max_amount})"


class Offer(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    banner = models.ImageField(upload_to='offer_banners/', blank=True, null=True)
    valid_until = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}: {self.subject}"


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=100, default='General')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.question
