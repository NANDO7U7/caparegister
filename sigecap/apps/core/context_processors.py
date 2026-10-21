from django.utils import timezone

def global_context(request):
    """
    Variables globales compartidas para todas las plantillas del sistema.
    """
    return {
        'APP_NAME': 'SIGECAP',
        'APP_FULL_NAME': 'Sistema de Gestión de Capacitaciones Docentes y Administrativas',
        'CURRENT_YEAR': timezone.now().year,
        'CURRENT_DATE': timezone.now().date(),
    }
