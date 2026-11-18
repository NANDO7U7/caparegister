"""Windows launcher tests using a fresh on-disk SQLite database per test."""

import hashlib
import os
import shutil
import secrets
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings


PROJECT = Path(__file__).resolve().parent
DRIVER = """
import os
import sys
from unittest.mock import patch
sys.path.insert(0, os.getcwd())
import local_windows as launcher

action, mode = sys.argv[1:]
if mode == 'admin':
    def answer(prompt):
        if 'Usuario' in prompt:
            return 'encargado'
        return 's'
    with patch('builtins.input', side_effect=answer), \\
         patch.object(sys.stdin, 'isatty', return_value=True), \\
         patch.object(sys.stderr, 'isatty', return_value=True), \\
         patch.object(launcher.getpass, 'getpass', return_value=os.environ['TEST_LOCAL_PASSWORD']), \\
         patch.object(launcher, 'start_server', side_effect=lambda: print('SERVIDOR')):
        sys.exit(launcher.main(action))
if mode == 'race':
    from threading import Barrier
    barrier = Barrier(2)
    import django
    os.environ['DJANGO_SETTINGS_MODULE'] = 'sigecap.local_settings'
    django.setup()
    from concurrent.futures import ThreadPoolExecutor
    from django.db import connections
    from django.contrib.auth import get_user_model
    def create(username):
        try:
            barrier.wait(timeout=10)
            return launcher.create_initial_admin(
                get_user_model()(username=username), os.environ['TEST_LOCAL_PASSWORD'])
        finally:
            connections.close_all()
    with ThreadPoolExecutor(2) as executor:
        assert sorted(executor.map(create, ['primero', 'segundo'])) == [False, True]
    sys.exit(0)
sys.exit(launcher.main(action))
"""


class LocalWindowsTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        shutil.copytree(PROJECT, self.directory, dirs_exist_ok=True, ignore=shutil.ignore_patterns(
            '*.sqlite3*', '.env', '__pycache__', 'media', 'staticfiles', 'test-results',
        ))
        self.database = self.directory / 'db.sqlite3'
        self.config = self.directory / '.env'
        self.password = secrets.token_urlsafe(24)

    def run_launcher(self, action='instalar', mode='', response='', **overrides):
        env = {
            key: value for key, value in os.environ.items()
            if not key.startswith(('DB_', 'DJANGO_', 'SIGECAP_'))
            and key not in {'SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS', 'USE_POSTGRES'}
        }
        env.update(TEST_LOCAL_PASSWORD=self.password, PYTHONIOENCODING='utf-8', **overrides)
        result = subprocess.run(
            [sys.executable, '-c', DRIVER, action, mode],
            cwd=self.directory, env=env, input=response, encoding='utf-8',
            capture_output=True, timeout=45,
        )
        output = result.stdout + result.stderr
        self.assertNotIn(self.password, output)
        return result.returncode, output

    def users(self):
        with closing(sqlite3.connect(self.database)) as connection:
            return connection.execute(
                'SELECT username, password, is_superuser FROM auth_user ORDER BY id'
            ).fetchall()

    def install_without_admin(self):
        code, output = self.run_launcher(response='s\n')
        self.assertEqual(code, 1, output)
        self.assertIn('consola local interactiva', output)
        self.assertEqual(self.users(), [])

    @override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.PBKDF2PasswordHasher'])
    def test_first_installation_and_second_launch(self):
        self.assertFalse(self.database.exists())
        code, output = self.run_launcher(mode='admin', DEBUG='invalid', USE_POSTGRES='True')
        self.assertEqual(code, 0, output)
        self.assertIn('Administrador inicial creado', output)
        self.assertTrue(self.config.is_file())
        username, stored, superuser = self.users()[0]
        self.assertEqual((username, superuser), ('encargado', 1))
        from django.contrib.auth.hashers import check_password
        self.assertTrue(check_password(self.password, stored))
        code, output = self.run_launcher('iniciar', mode='admin')
        self.assertEqual(code, 0, output)
        self.assertIn('SERVIDOR', output)
        self.assertEqual(len(self.users()), 1)

    def test_existing_database_and_configuration_are_preserved(self):
        self.install_without_admin()
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                """INSERT INTO auth_user
                   (username, password, is_superuser, is_staff, is_active, first_name, last_name, email, date_joined)
                   VALUES ('existente', '!', 1, 1, 1, '', '', '', '2026-01-01')"""
            )
        before = hashlib.sha256(self.database.read_bytes()).digest()
        configuration = self.config.read_bytes()
        code, output = self.run_launcher(mode='admin')
        self.assertEqual(code, 0, output)
        self.assertIn('Ya existe un superusuario activo', output)
        self.assertEqual(hashlib.sha256(self.database.read_bytes()).digest(), before)
        self.assertEqual(self.config.read_bytes(), configuration)

    def test_pending_migrations_on_existing_database(self):
        self.database.touch()
        code, output = self.run_launcher(mode='admin')
        self.assertEqual(code, 1, output)
        self.assertIn('Migraciones pendientes', output)
        self.assertEqual(self.database.read_bytes(), b'')

    def test_missing_configuration_declined_migrations_and_invalid_database(self):
        code, output = self.run_launcher('iniciar')
        self.assertEqual(code, 1, output)
        self.assertIn('Falta sigecap/.env', output)
        code, output = self.run_launcher(response='n\n')
        self.assertEqual(code, 1, output)
        self.assertIn('Instalación cancelada', output)
        self.assertFalse(self.database.exists())
        self.database.write_bytes(b'invalid')
        code, output = self.run_launcher(mode='admin')
        self.assertEqual(code, 1, output)
        self.assertIn('Error de SQLite', output)
        self.assertEqual(self.database.read_bytes(), b'invalid')

    def test_simultaneous_setup_creates_one_account_and_permanently_closes(self):
        self.install_without_admin()
        code, output = self.run_launcher(mode='race')
        self.assertEqual(code, 0, output)
        self.assertEqual(len(self.users()), 1)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('UPDATE auth_user SET is_active = 0')
        code, output = self.run_launcher('iniciar', mode='admin')
        self.assertEqual(code, 0, output)
        self.assertIn('ya se completó', output)
        self.assertEqual(len(self.users()), 1)


class NoWebSetupTests(SimpleTestCase):
    def test_server_opens_browser_only_when_bound_to_loopback(self):
        from local_windows import start_server

        def bound(address, port, handler, *, on_bind, **options):
            self.assertEqual((address, port), ('127.0.0.1', 8080))
            open_browser.assert_not_called()
            on_bind(port)

        with patch('django.core.management.commands.runserver.run', side_effect=bound) as run, \
             patch('django.core.management.commands.runserver.Command.check_migrations'), \
             patch('local_windows.webbrowser.open', return_value=True) as open_browser:
            start_server()
        run.assert_called_once()
        open_browser.assert_called_once_with('http://127.0.0.1:8080/')

    def test_remote_visitor_cannot_configure_administrator(self):
        response = self.client.post('/setup/', REMOTE_ADDR='203.0.113.10')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/', REMOTE_ADDR='203.0.113.10')
        self.assertRedirects(response, '/login/?next=/', fetch_redirect_response=False)
