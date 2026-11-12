from django.contrib import admin
from .models import AuditLog
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group


class SuperuserOnlyAdmin:
    """Account and group permissions must not provide an escalation path."""

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    has_add_permission = has_view_permission
    has_change_permission = has_view_permission
    has_delete_permission = has_view_permission


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class SigecapUserAdmin(SuperuserOnlyAdmin, UserAdmin):
    pass


@admin.register(Group)
class SigecapGroupAdmin(SuperuserOnlyAdmin, GroupAdmin):
    pass

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
