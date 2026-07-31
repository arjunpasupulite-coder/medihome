from django.urls import path
from . import views

app_name = 'telemedicine'

urlpatterns = [
    path('room/<int:consultation_id>/', views.telemedicine_room_view, name='room_detail'),
    path('room/', views.telemedicine_room_view, name='room'),
    path('send-message/<int:consultation_id>/', views.send_chat_message_view, name='send_message'),
    path('upload-prescription/<int:consultation_id>/', views.upload_prescription_view, name='upload_prescription'),
]
