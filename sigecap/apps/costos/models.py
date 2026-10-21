import uuid
from django.db import models
from apps.capacitaciones.models import Capacitacion
from apps.catalogos.models import Proyecto

class PresupuestoAnual(models.Model):
    """Presupuesto anual asignado a la unidad de capacitación o por proyecto."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anio = models.PositiveIntegerField(verbose_name="Año Fiscal")
    monto_total_asignado = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Monto Total Asignado (L/USD)")
    proyecto = models.ForeignKey(Proyecto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proyecto Asociado")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Notas del Presupuesto")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'presupuestos_anuales'
        verbose_name = 'Presupuesto Anual'
        verbose_name_plural = 'Presupuestos Anuales'
        ordering = ['-anio']

    def __str__(self):
        proj_name = f" - {self.proyecto.codigo}" if self.proyecto else ""
        return f"Presupuesto {self.anio}{proj_name}: {self.monto_total_asignado:,.2f}"


class GastoCapacitacion(models.Model):
    """Detalle de costos y gastos ejecutados o planificados por capacitación."""
    RUBROS = [
        ('Inscripción / Honorarios', 'Inscripción / Honorarios de Facilitador'),
        ('Materiales y Didácticos', 'Materiales y Recursos Didácticos'),
        ('Alimentación / Coffee Break', 'Alimentación / Refrigerios'),
        ('Transporte / Pasajes', 'Transporte y Movilización'),
        ('Viáticos y Hospedaje', 'Viáticos y Hospedaje'),
        ('Alquiler de Espacio / Plataforma', 'Alquiler de Espacio / Plataforma Virtual'),
        ('Certificación', 'Emisión de Certificados / Exámenes'),
        ('Otro', 'Otro Gasto'),
    ]
    ESTADOS = [
        ('Planificado', 'Planificado / Estimado'),
        ('Comprometido', 'Comprometido / Orden de Compra'),
        ('Ejecutado', 'Ejecutado / Pagado'),
        ('Cancelado', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capacitacion = models.ForeignKey(Capacitacion, on_delete=models.CASCADE, related_name='gastos', verbose_name="Capacitación")
    rubro = models.CharField(max_length=60, choices=RUBROS, verbose_name="Rubro de Gasto")
    monto_planificado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Monto Planificado")
    monto_ejecutado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Monto Ejecutado")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Planificado', verbose_name="Estado del Gasto")
    numero_comprobante = models.CharField(max_length=80, blank=True, null=True, verbose_name="N° Factura / Orden / Recibo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción o Justificación")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gastos_capacitaciones'
        verbose_name = 'Gasto de Capacitación'
        verbose_name_plural = 'Gastos y Costos de Capacitación'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.capacitacion.codigo} - {self.rubro}: L. {self.monto_ejecutado:,.2f}"
