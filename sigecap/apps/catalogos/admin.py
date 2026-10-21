from django.contrib import admin
from .models import Facultad, AreaFormacion, TipoModalidad, Proyecto, Proveedor

@admin.register(Facultad)
class FacultadAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'activo', 'created_at')
    list_filter = ('activo',)
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('codigo',)

@admin.register(AreaFormacion)
class AreaFormacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'activo', 'created_at')
    list_filter = ('activo',)
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('codigo',)

@admin.register(TipoModalidad)
class TipoModalidadAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'modalidad', 'activo')
    list_filter = ('tipo', 'modalidad', 'activo')
    search_fields = ('tipo', 'modalidad', 'descripcion')

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'fuente_financiamiento', 'presupuesto_asignado', 'activo')
    list_filter = ('fuente_financiamiento', 'activo')
    search_fields = ('codigo', 'nombre', 'fuente_financiamiento')

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'pais', 'contacto_nombre', 'contacto_email', 'activo')
    list_filter = ('tipo', 'pais', 'activo')
    search_fields = ('nombre', 'contacto_nombre', 'contacto_email')
