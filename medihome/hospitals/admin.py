from django.contrib import admin
from .models import HospitalProfile, Department, Doctor, Appointment

@admin.register(HospitalProfile)
class HospitalProfileAdmin(admin.ModelAdmin):
    list_display = ('hospital_name', 'license_number', 'emergency_contact', 'is_approved_by_admin', 'created_at')
    list_filter = ('is_approved_by_admin', 'created_at')
    search_fields = ('hospital_name', 'license_number', 'gst_number')
    actions = ['approve_hospitals']

    def approve_hospitals(self, request, queryset):
        queryset.update(is_approved_by_admin=True)
    approve_hospitals.short_description = "Approve selected hospitals"

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'hospital')
    list_filter = ('hospital',)
    search_fields = ('name', 'hospital__hospital_name')

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hospital', 'department', 'specialization', 'consultation_fee', 'experience_years')
    list_filter = ('hospital', 'department', 'specialization')
    search_fields = ('name', 'specialization', 'qualification', 'hospital__hospital_name')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_number', 'patient', 'hospital', 'doctor', 'appointment_date', 'status', 'payment_status')
    list_filter = ('status', 'payment_status', 'appointment_date')
    search_fields = ('appointment_number', 'patient__username', 'doctor__name', 'hospital__hospital_name')
