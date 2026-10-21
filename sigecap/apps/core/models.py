import uuid
from django.db import models
from django.contrib.auth.models import User

class AuditLog(models.Model):
    """
    Bitácora inmutable de auditoría para trazabilidad de cambios críticos.
    Cumple con lineamientos OWASP y políticas institucionales.
    """
    ACCIONES = [
        ('INSERT', 'Creación'),
        ('UPDATE', 'Modificación'),
        ('DELETE', 'Eliminación'),
        ('LOGIN', 'Inicio de Sesión'),
        ('EXPORT', 'Exportación de Datos'),
        ('IMPORT', 'Importación Masiva'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    tabla_afectada = models.CharField(max_length=80, verbose_name='Tabla o Módulo')
    registro_id = models.CharField(max_length=100, null=True, blank=True, verbose_name='ID de Registro')
    accion = models.CharField(max_length=20, choices=ACCIONES, verbose_name='Acción Realizada')
    detalles = models.JSONField(null=True, blank=True, verbose_name='Detalle de Cambios')
    ip_origen = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Origen')
    user_agent = models.TextField(null=True, blank=True, verbose_name='Navegador / Dispositivo')
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora')

    class Meta:
        db_table = 'auditoria_logs'
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Bitácora de Auditoría'
        ordering = ['-fecha_hora']

    def __str__(self):
        user_str = self.usuario.username if self.usuario else 'Sistema'
        return f"[{self.fecha_hora.strftime('%Y-%m-%d %H:%M')}] {user_str} - {self.accion} en {self.tabla_afectada}"
