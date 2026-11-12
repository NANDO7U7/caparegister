import io
import json
import secrets
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command, CommandError
from django.test import TestCase, SimpleTestCase
from django.urls import reverse

from apps.capacitaciones.models import Capacitacion
from apps.catalogos.models import Facultad, AreaFormacion, TipoModalidad, Proyecto, Proveedor
from sigecap.environment import configuration


class AuthorizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.normal = User.objects.create_user('normal')
        cls.staff = User.objects.create_user('staff', is_staff=True)
        cls.superuser = User.objects.create_superuser('superuser')
        cls.area = AreaFormacion.objects.create(codigo='AREA', nombre='Especialidad')
        cls.modalidad = TipoModalidad.objects.create(tipo='Taller', modalidad='Virtual')
        cls.proyecto = Proyecto.objects.create(codigo='IGA004', nombre='Proyecto')
        cls.proveedor = Proveedor.objects.create(nombre='No especificado')
        cls.cap = Capacitacion.objects.create(codigo='CAP', nombre='Evento', area_formacion=cls.area,
            tipo_modalidad=cls.modalidad, fecha_inicio='2026-01-01', fecha_fin='2026-01-01')

    def grant(self, user, app, *codenames):
        user.user_permissions.add(*Permission.objects.filter(content_type__app_label=app, codename__in=codenames))
        self.client.force_login(user)

    def test_anonymous_administrative_routes_redirect(self):
        for url in ('/administracion/', '/catalogos/', '/administracion/catalogo/facultad/crear/',
                    '/administracion/usuarios/crear/'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)

    def test_staff_flag_alone_and_normal_user_are_not_administrators(self):
        for user in (self.normal, self.staff):
            self.client.force_login(user)
            for url in ('/administracion/', '/catalogos/'):
                self.assertEqual(self.client.get(url).status_code, 403)
            for model in ('facultad', 'area', 'tipo_modalidad', 'proveedor', 'proyecto'):
                for action in ('crear', 'editar', 'eliminar'):
                    with self.subTest(user=user.username, model=model, action=action):
                        self.assertEqual(self.client.post(f'/administracion/catalogo/{model}/{action}/', {}).status_code, 403)
            self.assertEqual(self.client.post('/catalogos/', {'tipo_catalogo': 'facultad'}).status_code, 403)
            response = self.client.post(reverse('core:cambiar_estado_capacitacion', args=[self.cap.pk]), {'nuevo_estado': 'Cancelada'})
            self.assertEqual(response.status_code, 403)
        self.cap.refresh_from_db()
        self.assertEqual(self.cap.estado, 'Planificada')

    def test_regular_user_with_catalog_permission_still_needs_staff(self):
        self.grant(self.normal, 'catalogos', 'view_facultad', 'add_facultad')
        self.assertEqual(self.client.get('/catalogos/').status_code, 403)
        self.assertEqual(self.client.post('/administracion/catalogo/facultad/crear/',
            {'codigo': 'NO', 'nombre': 'No permitido'}).status_code, 403)
        self.assertFalse(Facultad.objects.exists())

    def test_delegated_staff_has_model_and_action_scoped_permissions(self):
        self.grant(self.staff, 'catalogos', 'view_facultad', 'add_facultad')
        self.assertEqual(self.client.get('/catalogos/').status_code, 200)
        panel = self.client.get('/administracion/')
        self.assertEqual(panel.status_code, 200)
        self.assertEqual(panel.context['usuarios'].count(), 0)
        self.assertEqual(panel.context['auditorias'].count(), 0)
        self.assertEqual(panel.context['areas'].count(), 0)
        self.assertEqual(self.client.post('/administracion/catalogo/facultad/crear/',
            {'codigo': 'OK', 'nombre': 'Permitida'}).status_code, 302)
        self.assertTrue(Facultad.objects.filter(codigo='OK').exists())
        for url in ('/administracion/?tab=usuarios', '/administracion/?tab=auditoria', '/administracion/?tab=capacitaciones'):
            self.assertEqual(self.client.get(url).status_code, 403)
        for action in ('editar', 'eliminar'):
            self.assertEqual(self.client.post(f'/administracion/catalogo/facultad/{action}/', {}).status_code, 403)
        self.assertEqual(self.client.post('/administracion/catalogo/area/crear/', {}).status_code, 403)

    def test_both_catalog_creation_routes_allow_authorized_staff(self):
        self.grant(self.staff, 'catalogos', 'add_facultad')
        self.assertEqual(self.client.post('/catalogos/', {'tipo_catalogo': 'facultad',
            'codigo': 'ALT', 'nombre': 'Permitida'}).status_code, 302)
        self.assertTrue(Facultad.objects.filter(codigo='ALT').exists())

    def test_accounts_remain_superuser_only_even_with_native_auth_permissions(self):
        self.grant(self.staff, 'auth', 'add_user', 'change_user', 'delete_user', 'view_user')
        before = get_user_model().objects.count()
        for action in ('crear', 'editar', 'password', 'eliminar'):
            response = self.client.post(f'/administracion/usuarios/{action}/', {'user_id': self.normal.pk})
            self.assertIn(response.status_code, (302, 403))
        self.assertEqual(get_user_model().objects.count(), before)
        self.normal.refresh_from_db()
        self.assertFalse(self.normal.is_superuser)

    def test_django_admin_cannot_be_used_to_escalate_accounts_or_groups(self):
        self.grant(self.staff, 'auth', 'view_user', 'add_user', 'change_user', 'delete_user',
                   'view_group', 'add_group', 'change_group', 'delete_group')
        for url in ('/admin/auth/user/', '/admin/auth/user/add/',
                    f'/admin/auth/user/{self.normal.pk}/change/', '/admin/auth/group/', '/admin/auth/group/add/'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get('/admin/auth/user/').status_code, 200)

    def test_superuser_can_manage_catalogs_and_open_all_tabs(self):
        self.client.force_login(self.superuser)
        for tab in ('catalogos', 'usuarios', 'capacitaciones', 'auditoria'):
            self.assertEqual(self.client.get('/administracion/', {'tab': tab}).status_code, 200)
        url = '/administracion/catalogo/facultad/'
        self.client.post(url + 'crear/', {'codigo': 'FAC', 'nombre': 'Original'})
        faculty = Facultad.objects.get(codigo='FAC')
        self.client.post(url + 'editar/', {'id': faculty.pk, 'nombre': 'Editada', 'codigo': 'FAC'})
        faculty.refresh_from_db()
        self.assertEqual(faculty.nombre, 'Editada')
        self.client.post(url + 'eliminar/', {'id': faculty.pk})
        self.assertFalse(Facultad.objects.filter(pk=faculty.pk).exists())

    def test_superuser_account_creation_enforces_password_validation(self):
        self.client.force_login(self.superuser)
        url = '/administracion/usuarios/crear/'
        self.client.post(url, {'username': 'managed_user', 'password': 'short', 'rol': 'CONSULTA'})
        self.assertFalse(get_user_model().objects.filter(username='managed_user').exists())
        password = secrets.token_urlsafe(32)
        self.client.post(url, {'username': 'managed_user', 'password': password, 'rol': 'CONSULTA'})
        user = get_user_model().objects.get(username='managed_user')
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_superuser)

    def test_normal_authorized_operator_keeps_normal_module_operations(self):
        self.grant(self.normal, 'personas', 'add_persona')
        self.assertEqual(self.client.get('/personas/nuevo/').status_code, 200)
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/capacitaciones/catalogo-clasico/').status_code, 200)

    def test_console_profile_uses_permissions_instead_of_usernames(self):
        self.client.force_login(self.normal)
        response = self.client.get('/capacitaciones/')
        self.assertFalse(response.context['current_user_profile']['can_edit'])
        self.assertEqual(response.context['current_user_profile']['rol'], 'CONSULTA')
        self.grant(self.normal, 'capacitaciones', 'add_capacitacion')
        response = self.client.get('/capacitaciones/')
        self.assertTrue(response.context['current_user_profile']['can_create'])
        self.assertFalse(response.context['current_user_profile']['can_edit'])

    def test_account_switch_rotates_csrf_and_keeps_logout_working(self):
        from django.test import Client
        password = secrets.token_urlsafe(32)
        self.staff.set_password(password)
        self.staff.save()
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.normal)
        client.get('/capacitaciones/')
        token = client.cookies['csrftoken'].value
        response = client.post('/capacitaciones/api/auth-login/',
            data=json.dumps({'username': self.staff.username, 'password': password}),
            content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(client.cookies['csrftoken'].value, token)
        self.assertEqual(client.post('/logout/', {'csrfmiddlewaretoken': response.json()['csrf_token']}).status_code, 302)

    def test_missing_functional_permissions_deny_mutations(self):
        self.client.force_login(self.normal)
        paths = [reverse('capacitaciones:inscribir', args=[self.cap.pk]),
                 reverse('capacitaciones:cargar_evidencia', args=[self.cap.pk]),
                 reverse('capacitaciones:eliminar', args=[self.cap.pk]),
                 '/capacitaciones/nueva/', '/personas/nuevo/', '/personas/matriz/matricular/']
        for url in paths:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_forged_client_roles_do_not_grant_permissions(self):
        self.client.force_login(self.normal)
        self.assertEqual(self.client.post('/capacitaciones/api/guardar-pif/',
            data=json.dumps({'nombre_evento': 'No', 'user_role': 'ADMIN', 'username': 'admin'}),
            content_type='application/json', HTTP_X_USER_ROLE='ADMIN').status_code, 403)

    def test_pif_add_and_change_are_distinct_and_existing_catalogs_remain_usable(self):
        self.grant(self.normal, 'capacitaciones', 'add_capacitacion')
        payload = {'nombre_evento': 'Permitido', 'fecha_inicio': '2026-01-01'}
        response = self.client.post('/capacitaciones/api/guardar-pif/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        payload['id'] = str(self.cap.pk)
        self.assertEqual(self.client.post('/capacitaciones/api/guardar-pif/', data=json.dumps(payload), content_type='application/json').status_code, 403)

    def test_pif_cannot_create_catalogs_indirectly_and_rolls_back(self):
        self.grant(self.staff, 'capacitaciones', 'add_capacitacion')
        self.grant(self.staff, 'catalogos', 'add_tipomodalidad')
        before = TipoModalidad.objects.count()
        response = self.client.post('/capacitaciones/api/guardar-pif/',
            data=json.dumps({'nombre_evento': 'No', 'tipo': 'Otro', 'area_pif': 'Nueva'}), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(TipoModalidad.objects.count(), before)
        self.assertEqual(Capacitacion.objects.count(), 1)

    def test_pif_provider_update_requires_catalog_permission(self):
        self.grant(self.normal, 'capacitaciones', 'add_capacitacion')
        response = self.client.post('/capacitaciones/api/guardar-pif/',
            data=json.dumps({'nombre_evento': 'No', 'contacto': 'Cambio no permitido'}), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.proveedor.refresh_from_db()
        self.assertIsNone(self.proveedor.contacto_nombre)

    def test_staff_with_course_permission_can_change_state(self):
        self.grant(self.staff, 'capacitaciones', 'view_capacitacion', 'change_capacitacion')
        self.assertEqual(self.client.get('/administracion/?tab=capacitaciones').status_code, 200)
        self.assertEqual(self.client.post(reverse('core:cambiar_estado_capacitacion', args=[self.cap.pk]),
            {'nuevo_estado': 'En Curso'}).status_code, 302)
        self.cap.refresh_from_db()
        self.assertEqual(self.cap.estado, 'En Curso')

    def test_import_cannot_bypass_catalog_permissions(self):
        import openpyxl
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.grant(self.staff, 'capacitaciones', 'add_capacitacion')
        self.grant(self.staff, 'catalogos', 'add_tipomodalidad')
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.append(['header'] * 23)
        row = [''] * 23
        row[0], row[5], row[7], row[14] = 'Otro', 'Importado', '2026-01-01', 'Nueva'
        sheet.append(row)
        data = io.BytesIO()
        workbook.save(data)
        before = TipoModalidad.objects.count()
        response = self.client.post('/capacitaciones/api/importar-excel-pif/', {
            'excel_file': SimpleUploadedFile('isolated.xlsx', data.getvalue()),
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(TipoModalidad.objects.count(), before)
        self.assertEqual(Capacitacion.objects.count(), 1)

    def test_unknown_update_never_falls_back_to_creation(self):
        from uuid import uuid4
        self.grant(self.normal, 'capacitaciones', 'change_capacitacion')
        response = self.client.post('/capacitaciones/api/guardar-pif/',
            data=json.dumps({'id': str(uuid4()), 'nombre_evento': 'No existe'}), content_type='application/json')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Capacitacion.objects.count(), 1)

    def test_seed_users_is_retired_without_touching_accounts(self):
        before = list(get_user_model().objects.values())
        with self.assertRaises(CommandError):
            call_command('seed_users', stdout=io.StringIO())
        self.assertEqual(list(get_user_model().objects.values()), before)


class EnvironmentTests(SimpleTestCase):
    def production(self, **extra):
        return {'SIGECAP_ENV': 'production', 'SECRET_KEY': secrets.token_urlsafe(64),
                'ALLOWED_HOSTS': 'sigecap.example.org', 'DB_ENGINE': 'django.db.backends.sqlite3',
                'DB_NAME': ':memory:', **extra}

    def test_production_fails_closed_without_required_environment(self):
        with self.assertRaises(ImproperlyConfigured):
            configuration({}, Path('.'))
        for name in ('SECRET_KEY', 'ALLOWED_HOSTS', 'DB_NAME'):
            env = self.production()
            env.pop(name)
            with self.subTest(name=name), self.assertRaises(ImproperlyConfigured):
                configuration(env, Path('.'))

    def test_debug_and_unsafe_hosts_and_weak_secret_are_rejected(self):
        for override in ({'DEBUG': 'True'}, {'DEBUG': 'release'}, {'ALLOWED_HOSTS': '*'},
                         {'SECRET_KEY': 'x' * 60}, {'SECRET_KEY': 'django-insecure-' + 'abcde' * 12}):
            with self.subTest(override=list(override)), self.assertRaises(ImproperlyConfigured):
                configuration(self.production(**override), Path('.'))

    def test_production_has_secure_defaults(self):
        values = configuration(self.production(), Path('.'))
        self.assertFalse(values['DEBUG'])
        for name in ('SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', 'SECURE_SSL_REDIRECT'):
            self.assertTrue(values[name])
        self.assertGreater(values['SECURE_HSTS_SECONDS'], 0)

    def test_postgres_requires_explicit_credentials(self):
        env = self.production(DB_ENGINE='django.db.backends.postgresql', DB_NAME='isolated',
                              DB_USER='example', DB_PASSWORD=secrets.token_urlsafe(32), DB_HOST='localhost')
        for missing in ('DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST'):
            with self.subTest(missing=missing), self.assertRaises(ImproperlyConfigured):
                configuration({k: v for k, v in env.items() if k != missing}, Path('.'))

    def test_explicit_local_profile_has_random_key_and_loopback_hosts(self):
        first = configuration({'SIGECAP_ENV': 'local'}, Path('.'))
        second = configuration({'SIGECAP_ENV': 'local'}, Path('.'))
        self.assertNotEqual(first['SECRET_KEY'], second['SECRET_KEY'])
        self.assertTrue(first['DEBUG'])
        self.assertFalse(first['SESSION_COOKIE_SECURE'])
        with self.assertRaises(ImproperlyConfigured):
            configuration({'SIGECAP_ENV': 'local', 'ALLOWED_HOSTS': 'example.org'}, Path('.'))

    def test_test_profile_ignores_external_database_and_secret(self):
        values = configuration({'SIGECAP_ENV': 'test', 'DB_ENGINE': 'django.db.backends.postgresql',
                                'DB_NAME': 'never_use_this_database', 'DEBUG': 'True'}, Path('.'))
        self.assertEqual(values['DATABASES']['default']['NAME'], ':memory:')
        self.assertFalse(values['DEBUG'])
