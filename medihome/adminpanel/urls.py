from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('users/', views.manage_users_view, name='manage_users'),
    path('labs/', views.manage_labs_view, name='manage_labs'),
    path('labs/toggle-approval/<int:lab_id>/', views.toggle_lab_approval_view, name='toggle_lab_approval'),
    path('hospitals/', views.manage_hospitals_view, name='manage_hospitals'),
    path('hospitals/toggle-approval/<int:hospital_id>/', views.toggle_hospital_approval_view, name='toggle_hospital_approval'),
    path('system-settings/', views.manage_system_settings_view, name='manage_system_settings'),
    path('symptom-mappings/', views.manage_symptom_mappings_view, name='manage_symptom_mappings'),
]
