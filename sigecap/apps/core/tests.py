import secrets
import re
from urllib.parse import urlsplit
from uuid import UUID

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import URLPattern, get_resolver, reverse


class AuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = secrets.token_urlsafe(24)
        cls.user = get_user_model().objects.create_user('usuario_prueba', password=cls.password)

    def sign_in(self, **extra):
        return self.client.post('/login/', {
            'username': self.user.username, 'password': self.password, **extra,
        })

    def test_anonymous_dashboard_redirect(self):
        self.assertRedirects(self.client.get('/'), '/login/?next=/')

    def test_login_form_is_public(self):
        response = self.client.get('/login/')
        self.assertContains(response, 'Nombre de usuario')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertNotContains(response, 'Dashboard Principal')

    def test_every_private_url_blocks_anonymous_get_and_post(self):
        def paths(patterns, prefix=''):
            for pattern in patterns:
                if not isinstance(pattern, URLPattern):
                    yield from paths(pattern.url_patterns, prefix + str(pattern.pattern))
                    continue
                route = str(pattern.pattern)
                for name, converter in getattr(pattern.pattern, 'converters', {}).items():
                    value = str(UUID(int=1)) if converter.__class__.__name__ == 'UUIDConverter' else '1'
                    route = re.sub(r'<(?:\w+:)?' + name + r'>', value, route)
                yield '/' + prefix + route

        for path in paths(get_resolver().url_patterns):
            if path in ('/login/', '/admin/login/') or path.startswith('/^'):
                continue
            for method in ('get', 'post'):
                with self.subTest(path=path, method=method):
                    response = getattr(self.client, method)(path)
                    self.assertEqual(response.status_code, 302)
                    self.assertIn(urlsplit(response.url).path, ('/login/', '/admin/login/'))
                    if urlsplit(response.url).path == '/admin/login/':
                        self.assertEqual(urlsplit(self.client.get(response.url).url).path, '/login/')

    def test_login_success_and_dashboard(self):
        self.assertRedirects(self.sign_in(), '/')
        self.assertContains(self.client.get('/'), 'Dashboard Principal')

    def test_private_destination_including_query(self):
        target = reverse('personas:lista') + '?q=docente'
        self.assertRedirects(self.sign_in(next=target), target)

    def test_unsafe_destinations_fall_back_to_dashboard(self):
        for target in ('https://evil.example/', '//evil.example/', 'http://testserver.evil.example/'):
            with self.subTest(target=target):
                self.client.logout()
                self.assertRedirects(self.sign_in(next=target), '/')

    def test_bad_and_inactive_credentials_use_same_generic_error(self):
        for username in (self.user.username, 'no_existe'):
            response = self.client.post('/login/', {'username': username, 'password': 'incorrecta'})
            self.assertContains(response, 'No se pudo iniciar sesión.')
            self.assertNotIn('_auth_user_id', self.client.session)
        self.user.is_active = False
        self.user.save()
        self.assertContains(self.sign_in(), 'No se pudo iniciar sesión.')

    def test_logout_is_post_only_and_invalidates_session(self):
        self.sign_in()
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        old_session = self.client.cookies['sessionid'].value
        self.assertRedirects(self.client.post('/logout/', {'next': '/personas/'}), '/login/')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.client.cookies['sessionid'] = old_session
        self.assertRedirects(self.client.get('/'), '/login/?next=/')

    def test_csrf_login_logout_and_mutation(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/login/', {}).status_code, 403)
        client.get('/login/')
        token = client.cookies['csrftoken'].value
        response = client.post('/login/', {'username': self.user.username, 'password': self.password,
                                           'csrfmiddlewaretoken': token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.post('/logout/').status_code, 403)
        self.assertEqual(client.post('/capacitaciones/api/guardar-pif/', {}).status_code, 403)
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post('/logout/', {'csrfmiddlewaretoken': token}).status_code, 302)

    def test_role_switch_cannot_impersonate(self):
        self.sign_in()
        self.client.post('/conmutar-rol/', {'username': 'admin'})
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))
        self.assertFalse(get_user_model().objects.filter(username='ugb_pif').exists())

    def test_regular_user_cannot_manage_accounts(self):
        self.sign_in()
        before = get_user_model().objects.count()
        response = self.client.post('/administracion/usuarios/crear/', {'username': 'intruso'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_user_model().objects.count(), before)

    def test_admin_login_uses_main_login(self):
        self.assertRedirects(self.client.get('/admin/login/'), '/login/?next=/admin/')

    def test_media_is_private(self):
        from django.conf.urls.static import static
        from django.test import override_settings
        from types import ModuleType
        urlconf = ModuleType('private_media_test_urls')
        with self.settings(DEBUG=True):
            urlconf.urlpatterns = static('/media/', document_root='/unused')
        with override_settings(ROOT_URLCONF=urlconf):
            response = self.client.get('/media/documento.pdf')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(urlsplit(response.url).path, '/login/')

    def test_private_pages_are_not_cached(self):
        self.sign_in()
        self.assertIn('no-store', self.client.get('/')['Cache-Control'])
