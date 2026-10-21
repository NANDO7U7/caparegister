from django.urls import path
from . import views

app_name = 'personas'

urlpatterns = [
    path('', views.lista_personas, name='lista'),
    path('nuevo/', views.crear_persona, name='crear'),
    path('portal/', views.portal_docente_view, name='portal_docente'),
    path('matriz/', views.matriz_docente_view, name='matriz_docente'),
    path('matriz/matricular/', views.matricular_docente_matriz, name='matricular_docente_matriz'),
    path('<uuid:pk>/', views.ficha_persona, name='ficha'),
    path('<uuid:pk>/editar/', views.editar_persona, name='editar'),
    path('<uuid:pk>/constancia-pdf/', views.descargar_constancia_pdf, name='descargar_constancia_pdf'),
]
