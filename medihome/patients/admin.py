from django.contrib import admin
from .models import PatientProfile, MedicineReminder, Wishlist

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_group', 'gender', 'dob', 'emergency_contact')
    list_filter = ('blood_group', 'gender')
    search_fields = ('user__username', 'user__email', 'emergency_contact')

@admin.register(MedicineReminder)
class MedicineReminderAdmin(admin.ModelAdmin):
    list_display = ('medicine_name', 'patient', 'morning', 'afternoon', 'night', 'duration_days', 'start_date')
    list_filter = ('morning', 'afternoon', 'night', 'start_date')
    search_fields = ('medicine_name', 'patient__user__username')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'diagnostic_test', 'doctor', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'diagnostic_test__name', 'doctor__name')
