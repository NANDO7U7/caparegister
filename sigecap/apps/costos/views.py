from django.shortcuts import render
from django.db.models import Sum
from .models import PresupuestoAnual, GastoCapacitacion
from apps.capacitaciones.models import Capacitacion

def dashboard_costos(request):
    """
    Control de Costos y Presupuesto de Formaciones (Inspirado en Prototipo Google Stitch).
    Calcula Presupuesto Asignado vs. Ejecutado y comparativa por rubros.
    """
    total_presupuesto = PresupuestoAnual.objects.aggregate(total=Sum('monto_total_asignado'))['total'] or 0
    total_planificado = GastoCapacitacion.objects.aggregate(total=Sum('monto_planificado'))['total'] or 0
    total_ejecutado = GastoCapacitacion.objects.filter(estado='Ejecutado').aggregate(total=Sum('monto_ejecutado'))['total'] or 0
    saldo_disponible = total_presupuesto - total_ejecutado

    # Gastos Recientes
    gastos = GastoCapacitacion.objects.select_related('capacitacion').order_by('-created_at')[:15]

    # Desglose por Rubros
    rubros_summary = GastoCapacitacion.objects.values('rubro').annotate(
        total_ejecutado=Sum('monto_ejecutado'),
        total_planificado=Sum('monto_planificado')
    ).order_by('-total_ejecutado')

    context = {
        'total_presupuesto': total_presupuesto,
        'total_planificado': total_planificado,
        'total_ejecutado': total_ejecutado,
        'saldo_disponible': saldo_disponible,
        'gastos': gastos,
        'rubros_summary': rubros_summary,
    }
    return render(request, 'costos/presupuesto.html', context)
