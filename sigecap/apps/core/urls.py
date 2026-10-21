from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('administracion/', views.panel_administracion_view, name='panel_administracion'),
    path('administracion/catalogo/<str:modelo>/<str:accion>/', views.catalogo_crud_view, name='catalogo_crud'),
    path('administracion/usuarios/<str:accion>/', views.usuario_crud_view, name='usuario_crud'),
    path('administracion/capacitacion/<uuid:pk>/cambiar-estado/', views.cambiar_estado_capacitacion_view, name='cambiar_estado_capacitacion'),
    path('conmutar-rol/', views.conmutar_rol_web_view, name='conmutar_rol'),
]
