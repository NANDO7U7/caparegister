import re
import time

from django.db import IntegrityError, OperationalError, transaction

from .forms import PersonaForm
from .models import CompetenciaMatriz, MatriculaMatrizDocente, Persona


def siguiente_codigo():
    mayor = 0
    for codigo in Persona.objects.values_list('codigo_empleado', flat=True).iterator():
        if re.fullmatch(r'EMP-[0-9]+', codigo):
            mayor = max(mayor, int(codigo[4:]))
    return f'EMP-{mayor + 1:04d}'


def registrar_persona(data, automatico):
    """La restricción única decide el ganador; cada reintento usa otra transacción."""
    data = data.copy()
    form = PersonaForm(data)
    for intento in range(10):
        try:
            if automatico:
                data['codigo_empleado'] = siguiente_codigo()
            form = PersonaForm(data)
            if not form.is_valid():
                if automatico and set(form.errors) == {'codigo_empleado'}:
                    continue
                return form, None
            with transaction.atomic():
                persona = form.save()
                if persona.tipo_personal in ['Docente', 'Ambos']:
                    for comp in CompetenciaMatriz.objects.filter(activo=True):
                        MatriculaMatrizDocente.objects.get_or_create(
                            persona=persona, competencia=comp,
                            defaults={'estado': 'Pendiente'},
                        )
            return form, persona
        except IntegrityError:
            # Revalidar después del rollback también detecta documento/correo duplicados.
            if not automatico:
                break
        except OperationalError as error:
            # SQLite serializa escrituras y puede rechazar una transacción ocupada.
            if 'locked' not in str(error).lower() and 'busy' not in str(error).lower():
                raise
        time.sleep(0.02 * (intento + 1))
    form.add_error(None, 'No se pudo guardar: existe un conflicto con otro registro. Revise el código, documento y correo e intente nuevamente.')
    return form, None
