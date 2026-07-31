from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_type', 'target_id', 'rating', 'star_display', 'created_at')
    list_filter = ('target_type', 'rating', 'created_at')
    search_fields = ('user__username', 'comment', 'target_id')
