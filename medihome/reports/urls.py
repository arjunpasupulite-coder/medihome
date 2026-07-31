from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('list/', views.report_list_view, name='list'),
    path('upload/<int:booking_id>/', views.upload_report_view, name='upload_report'),
    path('view/<int:report_id>/', views.view_report_view, name='view_report'),
    path('download/<int:report_id>/', views.download_report_pdf_view, name='download_report'),
    path('request-hard-copy/<int:report_id>/', views.request_hard_copy_view, name='request_hard_copy'),
]
