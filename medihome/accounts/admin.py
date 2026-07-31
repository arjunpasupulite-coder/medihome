from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ActivityLog

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'phone_number', 'is_staff', 'created_at')
    list_filter = ('role', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('-created_at',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('MediHome Attributes', {'fields': ('role', 'phone_number', 'profile_picture', 'address', 'latitude', 'longitude')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('MediHome Attributes', {'fields': ('role', 'phone_number', 'address')}),
    )

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'ip_address')
    list_filter = ('timestamp', 'action')
    search_fields = ('user__username', 'action', 'ip_address', 'details')
    readonly_fields = ('user', 'action', 'ip_address', 'details', 'timestamp')
