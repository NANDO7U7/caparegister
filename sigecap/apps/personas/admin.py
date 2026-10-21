from django.contrib import admin
from .models import Persona, CompetenciaMatriz, MatriculaMatrizDocente

class MatriculaMatrizInline(admin.TabularInline):
    model = MatriculaMatrizDocente
    extra = 1
    autocomplete_fields = ['competencia']

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('codigo_empleado', 'nombre_completo', 'tipo_personal', 'tipo_contrato', 'grado_academico', 'facultad', 'activo')
    list_filter = ('tipo_personal', 'tipo_contrato', 'grado_academico', 'facultad', 'activo')
    search_fields = ('codigo_empleado', 'documento_identidad', 'nombres', 'apellidos', 'email_institucional')
    ordering = ('apellidos', 'nombres')
    inlines = [MatriculaMatrizInline]

@admin.register(CompetenciaMatriz)
class CompetenciaMatrizAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'orden', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('categoria', 'orden')

@admin.register(MatriculaMatrizDocente)
class MatriculaMatrizDocenteAdmin(admin.ModelAdmin):
    list_display = ('persona', 'competencia', 'estado', 'fecha_completado', 'updated_at')
    list_filter = ('estado', 'competencia__categoria')
    search_fields = ('persona__nombres', 'persona__apellidos', 'persona__codigo_empleado', 'competencia__nombre')
    autocomplete_fields = ['persona', 'competencia']
