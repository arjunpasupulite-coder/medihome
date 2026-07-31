from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('feed/', views.feed_view, name='feed'),
]
