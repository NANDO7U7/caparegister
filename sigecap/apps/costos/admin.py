from django.contrib import admin
from .models import PresupuestoAnual, GastoCapacitacion

@admin.register(PresupuestoAnual)
class PresupuestoAnualAdmin(admin.ModelAdmin):
    list_display = ('anio', 'monto_total_asignado', 'proyecto', 'created_at')
    list_filter = ('anio', 'proyecto')

@admin.register(GastoCapacitacion)
class GastoCapacitacionAdmin(admin.ModelAdmin):
    list_display = ('capacitacion', 'rubro', 'monto_planificado', 'monto_ejecutado', 'estado', 'numero_comprobante')
    list_filter = ('rubro', 'estado', 'capacitacion__area_formacion')
    search_fields = ('capacitacion__codigo', 'capacitacion__nombre', 'numero_comprobante', 'descripcion')
    autocomplete_fields = ['capacitacion']
