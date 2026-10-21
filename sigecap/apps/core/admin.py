from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'usuario', 'accion', 'tabla_afectada', 'registro_id', 'ip_origen')
    list_filter = ('accion', 'tabla_afectada', 'fecha_hora')
    search_fields = ('usuario__username', 'tabla_afectada', 'registro_id', 'ip_origen')
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
