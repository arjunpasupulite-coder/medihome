from django.contrib import admin
from .models import TelemedicineConsultation, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender', 'message', 'timestamp')

@admin.register(TelemedicineConsultation)
class TelemedicineConsultationAdmin(admin.ModelAdmin):
    list_display = ('video_room_id', 'patient', 'doctor', 'scheduled_time', 'status', 'created_at')
    list_filter = ('status', 'scheduled_time')
    search_fields = ('video_room_id', 'patient__username', 'doctor__name')
    inlines = [ChatMessageInline]

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'sender', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('sender__username', 'message')
