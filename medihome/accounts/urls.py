from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/patient/', views.login_patient_view, name='login_patient'),
    path('login/diagnostician/', views.login_diagnostician_view, name='login_diagnostician'),
    path('login/hospital/', views.login_hospital_view, name='login_hospital'),
    path('register/patient/', views.register_patient_view, name='register_patient'),
    path('register/diagnostician/', views.register_diagnostician_view, name='register_diagnostician'),
    path('register/hospital/', views.register_hospital_view, name='register_hospital'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
]
