"""
URL configuration for SIGECAP project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('catalogos/', include('apps.catalogos.urls')),
    path('personas/', include('apps.personas.urls')),
    path('capacitaciones/', include('apps.capacitaciones.urls')),
    path('costos/', include('apps.costos.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personalización del panel administrativo Django Admin
admin.site.site_header = "SIGECAP — Panel de Administración"
admin.site.site_title = "SIGECAP Admin"
admin.site.index_title = "Gestión de Datos y Catálogos Universitarios"
