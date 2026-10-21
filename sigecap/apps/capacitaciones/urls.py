from django.urls import path
from . import views

app_name = 'capacitaciones'

urlpatterns = [
    path('', views.sistema_gestion_view, name='lista'),
    path('sistema-gestion/', views.sistema_gestion_view, name='sistema_gestion'),
    path('catalogo-clasico/', views.lista_capacitaciones, name='lista_clasica'),
    path('api/auth-login/', views.auth_login_api, name='auth_login'),
    path('api/guardar-pif/', views.guardar_capacitacion_pif_api, name='guardar_pif'),
    path('api/eliminar-pif/<uuid:pk>/', views.eliminar_capacitacion_pif_api, name='eliminar_pif'),
    path('api/importar-excel-pif/', views.importar_excel_pif_api, name='importar_excel_pif'),
    path('exportar-excel-pif/', views.exportar_excel_pif, name='exportar_excel_pif'),
    path('nueva/', views.crear_capacitacion, name='crear'),
    path('calendario/', views.calendario_view, name='calendario'),
    path('<uuid:pk>/', views.detalle_capacitacion, name='detalle'),
    path('<uuid:pk>/editar/', views.editar_capacitacion, name='editar'),
    path('<uuid:pk>/duplicar/', views.duplicar_capacitacion, name='duplicar'),
    path('<uuid:pk>/qr-asistencia/', views.qr_asistencia_view, name='qr_asistencia'),
    path('<uuid:pk>/asistencia-qr/', views.registrar_asistencia_qr, name='asistencia_qr'),
    path('<uuid:pk>/inscribir/', views.inscribir_participante, name='inscribir'),
    path('<uuid:pk>/cargar-evidencia/', views.cargar_evidencia_view, name='cargar_evidencia'),
    path('<uuid:pk>/encuesta/', views.responder_encuesta, name='encuesta'),
    path('<uuid:pk>/eliminar/', views.eliminar_capacitacion_view, name='eliminar'),
    path('<uuid:pk>/participantes/<uuid:part_id>/eliminar/', views.eliminar_participante_view, name='eliminar_participante'),
    path('<uuid:pk>/evidencias/<uuid:evidencia_id>/eliminar/', views.eliminar_evidencia_view, name='eliminar_evidencia'),
]
