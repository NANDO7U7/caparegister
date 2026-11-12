"""Start an isolated browser-test server. Never opens the application database."""
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'sigecap.e2e_settings'

import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command

assert settings.DATABASES['default']['NAME'] == 'file:sigecap-browser-tests?mode=memory&cache=shared'
passwords = {role: os.environ[f'SIGECAP_E2E_{role}_PASSWORD'] for role in ('ADMIN', 'PIF', 'COORD', 'CONSULTA')}
call_command('migrate', verbosity=0, interactive=False)
User = get_user_model()
User.objects.create_superuser('admin', password=passwords['ADMIN'])
pif = User.objects.create_user('ugb_pif', password=passwords['PIF'], is_staff=True)
pif.user_permissions.set(Permission.objects.filter(content_type__app_label__in=['capacitaciones', 'catalogos', 'personas']))
for username, role in (('coordinador', 'COORD'), ('consulta', 'CONSULTA')):
    user = User.objects.create_user(username, password=passwords[role])
    user.user_permissions.set(Permission.objects.filter(codename__startswith='view_'))
from apps.catalogos.models import AreaFormacion, TipoModalidad
from apps.capacitaciones.models import Capacitacion

Capacitacion.objects.create(
    codigo='E2E-001', nombre='Evento aislado de pruebas',
    area_formacion=AreaFormacion.objects.create(codigo='E2E', nombre='Especialidad'),
    tipo_modalidad=TipoModalidad.objects.create(tipo='Taller', modalidad='Virtual'),
    fecha_inicio='2026-01-01', fecha_fin='2026-01-01',
)
call_command('runserver', '127.0.0.1:8091', use_reloader=False)
