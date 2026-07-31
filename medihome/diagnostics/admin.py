from django.contrib import admin
from .models import (
    DiagnosticianProfile, DiagnosticTest, Symptom, SymptomTestMapping,
    Technician, Cart, CartItem, Booking, BookingItem, BookingStatusHistory
)

@admin.register(DiagnosticianProfile)
class DiagnosticianProfileAdmin(admin.ModelAdmin):
    list_display = ('lab_name', 'owner_name', 'license_number', 'is_home_collection_available', 'is_approved_by_admin', 'created_at')
    list_filter = ('is_approved_by_admin', 'is_home_collection_available', 'nabl_accredited')
    search_fields = ('lab_name', 'owner_name', 'license_number', 'gst_number')
    actions = ['approve_labs']

    def approve_labs(self, request, queryset):
        queryset.update(is_approved_by_admin=True)
    approve_labs.short_description = "Approve selected laboratories"

@admin.register(DiagnosticTest)
class DiagnosticTestAdmin(admin.ModelAdmin):
    list_display = ('name', 'lab', 'category', 'price', 'duration_hours', 'is_home_collection_compatible')
    list_filter = ('category', 'is_home_collection_compatible', 'lab')
    search_fields = ('name', 'category', 'lab__lab_name')

@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(SymptomTestMapping)
class SymptomTestMappingAdmin(admin.ModelAdmin):
    list_display = ('symptom', 'test_name', 'frequency_weight', 'star_display')
    list_filter = ('frequency_weight', 'symptom')
    search_fields = ('symptom__name', 'test_name')

@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ('name', 'lab', 'phone', 'area', 'is_available')
    list_filter = ('is_available', 'lab')
    search_fields = ('name', 'phone', 'area', 'lab__lab_name')

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    inlines = [CartItemInline]

class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 0

class BookingStatusHistoryInline(admin.TabularInline):
    model = BookingStatusHistory
    extra = 0
    readonly_fields = ('status', 'updated_by', 'notes', 'timestamp')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_number', 'patient', 'diagnostician', 'grand_total', 'status', 'collection_date', 'created_at')
    list_filter = ('status', 'collection_date', 'created_at')
    search_fields = ('booking_number', 'patient__username', 'diagnostician__lab_name')
    inlines = [BookingItemInline, BookingStatusHistoryInline]

@admin.register(BookingStatusHistory)
class BookingStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('booking', 'status', 'updated_by', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('booking__booking_number', 'notes')
