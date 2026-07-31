from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

def landing_view(request):
    return render(request, 'landing.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_view, name='landing'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('patients/', include('patients.urls', namespace='patients')),
    path('diagnostics/', include('diagnostics.urls', namespace='diagnostics')),
    path('hospitals/', include('hospitals.urls', namespace='hospitals')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('telemedicine/', include('telemedicine.urls', namespace='telemedicine')),
    path('adminpanel/', include('adminpanel.urls', namespace='adminpanel')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
