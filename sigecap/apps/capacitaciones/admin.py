from django.contrib import admin
from .models import Capacitacion, Participacion, Evidencia, EncuestaSatisfaccion

class ParticipacionInline(admin.TabularInline):
    model = Participacion
    extra = 1
    autocomplete_fields = ['persona']

class EvidenciaInline(admin.TabularInline):
    model = Evidencia
    extra = 1

class EncuestaSatisfaccionInline(admin.TabularInline):
    model = EncuestaSatisfaccion
    extra = 0
    readonly_fields = ['puntaje_general', 'created_at']

@admin.register(Capacitacion)
class CapacitacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'area_formacion', 'tipo_modalidad', 'estado', 'horas_duracion', 'fecha_inicio', 'fecha_fin')
    list_filter = ('estado', 'area_formacion', 'tipo_modalidad', 'fecha_inicio')
    search_fields = ('codigo', 'nombre', 'descripcion')
    filter_horizontal = ('facultades',)
    inlines = [ParticipacionInline, EvidenciaInline, EncuestaSatisfaccionInline]
    date_hierarchy = 'fecha_inicio'

@admin.register(Participacion)
class ParticipacionAdmin(admin.ModelAdmin):
    list_display = ('persona', 'capacitacion', 'estado_asistencia', 'calificacion', 'horas_acreditadas', 'certificado_emitido')
    list_filter = ('estado_asistencia', 'certificado_emitido', 'capacitacion__area_formacion')
    search_fields = ('persona__nombres', 'persona__apellidos', 'persona__codigo_empleado', 'capacitacion__codigo', 'capacitacion__nombre')
    autocomplete_fields = ['persona', 'capacitacion']

@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre_original', 'tipo_evidencia', 'capacitacion', 'tamano_bytes', 'created_at')
    list_filter = ('tipo_evidencia', 'created_at')
    search_fields = ('nombre_original', 'capacitacion__codigo', 'capacitacion__nombre')

@admin.register(EncuestaSatisfaccion)
class EncuestaSatisfaccionAdmin(admin.ModelAdmin):
    list_display = ('capacitacion', 'participante', 'puntaje_general', 'claridad_facilitador', 'dominio_tema', 'utilidad_practica', 'created_at')
    list_filter = ('capacitacion__area_formacion', 'created_at')
    search_fields = ('capacitacion__codigo', 'capacitacion__nombre', 'participante__nombres', 'participante__apellidos')
