from django.contrib import admin
from .models import SystemSettings, Payment, Invoice, Coupon, Offer, ContactMessage, FAQ

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('gst_percentage', 'platform_fee', 'home_collection_charge', 'support_email', 'updated_at')
    
    def has_add_permission(self, request):
        # Enforce singleton pattern: block adding secondary configuration object
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'booking_type', 'reference_id', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('booking_type', 'payment_method', 'status', 'created_at')
    search_fields = ('transaction_id', 'reference_id', 'user__username')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'payment', 'created_at')
    search_fields = ('invoice_number', 'payment__transaction_id')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'discount_max_amount', 'min_order_amount', 'valid_until', 'is_active', 'used_count', 'usage_limit')
    list_filter = ('is_active', 'valid_until')
    search_fields = ('code',)

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'discount_percentage', 'valid_until', 'is_active')
    list_filter = ('is_active', 'valid_until')
    search_fields = ('title', 'description')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
