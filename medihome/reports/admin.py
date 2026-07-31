from django.contrib import admin
from .models import MedicalReport

@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('report_title', 'patient', 'report_type', 'is_hard_copy_requested', 'created_at')
    list_filter = ('report_type', 'is_hard_copy_requested', 'created_at')
    search_fields = ('report_title', 'patient__username', 'summary_notes')
