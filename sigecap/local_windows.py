"""Entry point for the local Windows launchers. No browser-based setup."""

import getpass
import os
import sys
import warnings
import webbrowser
from pathlib import Path
from secrets import token_hex


BASE_DIR = Path(__file__).resolve().parent
ADDRESS = '127.0.0.1:8080'
CONFIG_VARIABLES = (
    'SIGECAP_ENV', 'SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS', 'USE_POSTGRES',
    'DB_ENGINE', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT',
)


def prepare_configuration():
    try:
        with (BASE_DIR / '.env').open('x', encoding='utf-8') as config:
            # Hex characters avoid dotenv interpolation and quoting issues.
            config.write(
                'SIGECAP_ENV=local\nDEBUG=True\n'
                'ALLOWED_HOSTS=127.0.0.1,localhost\n'
                'DB_ENGINE=django.db.backends.sqlite3\n'
                f'SECRET_KEY={token_hex(32)}\n'
            )
    except FileExistsError:
        pass


def check_database(database, *, install):
    from django.core.management import CommandError, call_command
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    new_database = not database.exists()
    if new_database:
        if not install:
            raise CommandError('Falta la base de datos. Ejecuta instalar.bat.')
        print(f'Se creará una base de datos nueva en {database}')
        if input('¿Aplicar las migraciones iniciales? [s/N] ').strip().lower() != 's':
            raise CommandError('Instalación cancelada antes de crear la base de datos.')
        # Reserve the path exclusively. A second installer cannot initialize it.
        try:
            database.touch(exist_ok=False)
        except FileExistsError as error:
            raise CommandError('La base apareció durante la instalación. Vuelve a ejecutar instalar.bat.') from error
    call_command('check')
    if new_database:
        call_command('migrate', interactive=False)

    executor = MigrationExecutor(connection)
    executor.loader.check_consistent_history(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    if plan:
        pending = ', '.join(f'{migration.app_label}.{migration.name}' for migration, _ in plan)
        raise CommandError(
            f'Migraciones pendientes: {pending}. Pide a soporte que revise la base '
            'y haga un respaldo antes de actualizarla.'
        )


def setup_status(users, cursor):
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'sigecap_local_setup'"
    )
    if cursor.fetchone():
        return 'completed'
    if users.filter(is_active=True, is_superuser=True).exists():
        return 'active'
    return 'needed'


def create_initial_admin(user, password):
    from django.db import connection, transaction

    with transaction.atomic(), connection.cursor() as cursor:
        # Acquire SQLite's write lock before rechecking the account and marker.
        # A failure rolls back both the marker table and the account.
        cursor.execute('CREATE TABLE IF NOT EXISTS sigecap_local_setup (completed INTEGER)')
        cursor.execute('SELECT 1 FROM sigecap_local_setup LIMIT 1')
        users = type(user)._default_manager
        if cursor.fetchone() or users.filter(is_active=True, is_superuser=True).exists():
            transaction.set_rollback(True)
            return False
        users.create_superuser(username=user.username, password=password)
        cursor.execute('INSERT INTO sigecap_local_setup (completed) VALUES (1)')
        return True


def configure_admin():
    from django.contrib.auth import get_user_model, password_validation
    from django.core.management import CommandError
    from django.db import connection

    user_model = get_user_model()
    with connection.cursor() as cursor:
        status = setup_status(user_model._default_manager, cursor)
    if status == 'active':
        print('Ya existe un superusuario activo.')
        return
    if status == 'completed':
        print('La configuración inicial del administrador ya se completó.')
        return
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        raise CommandError('Abre el archivo .bat en una consola local interactiva.')
    print('Asistente local de configuración del administrador inicial.')
    if input('¿Crear la cuenta administradora? [s/N] ').strip().lower() != 's':
        raise CommandError('Configuración inicial aplazada. Ejecuta instalar.bat o iniciar.bat para retomarla.')
    user = user_model(username=input('Usuario del administrador: ').strip())
    user.full_clean(exclude=['password'])
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        password = getpass.getpass('Contraseña: ')
        confirmation = getpass.getpass('Repite la contraseña: ')
    if not password or password != confirmation:
        raise CommandError('Escribe una contraseña y repítela exactamente.')
    password_validation.validate_password(password, user)
    if create_initial_admin(user, password):
        print('Administrador inicial creado.')
    else:
        print('Otro proceso ya configuró el administrador.')


def start_server():
    from django.contrib.staticfiles.management.commands.runserver import Command
    from django.core.management import call_command

    class LocalRunServer(Command):
        def on_bind(self, server_port):
            super().on_bind(server_port)
            url = f'http://{ADDRESS}/'
            try:
                if webbrowser.open(url):
                    return
            except OSError:
                pass
            print(f'Abre {url} en tu navegador.')

    call_command(LocalRunServer(), ADDRESS, use_reloader=False)


def main(action):
    try:
        import django
        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured, ValidationError
        from django.core.management import CommandError
        from django.db import DatabaseError
        from django.db.migrations.exceptions import (
            BadMigrationError, InconsistentMigrationHistory, InvalidBasesError, NodeNotFoundError,
        )
    except ImportError:
        print('Faltan dependencias. Ejecuta instalar.bat.', file=sys.stderr)
        return 1

    try:
        os.chdir(BASE_DIR)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'sigecap.local_settings'
        # The launchers use their own .env even on a machine with other projects.
        for variable in CONFIG_VARIABLES:
            os.environ.pop(variable, None)
        if action == 'instalar':
            prepare_configuration()
        elif not (BASE_DIR / '.env').is_file():
            raise CommandError('Falta sigecap/.env. Ejecuta instalar.bat.')
        django.setup()
        config = settings.DATABASES['default']
        name = str(config['NAME'])
        if (
            config['ENGINE'] != 'django.db.backends.sqlite3'
            or not name.strip() or name == ':memory:' or name.lower().startswith('file:')
        ):
            raise CommandError('El instalador de Windows requiere una base SQLite en un archivo local.')
        database = Path(name).absolute()
        check_database(database, install=action == 'instalar')
        configure_admin()
        if action == 'iniciar':
            start_server()
    except ImportError as error:
        print(f'Falta una dependencia ({error.name}). Ejecuta instalar.bat.', file=sys.stderr)
        return 1
    except (CommandError, ImproperlyConfigured, ValidationError, OSError,
            BadMigrationError, InconsistentMigrationHistory, InvalidBasesError,
            NodeNotFoundError, getpass.GetPassWarning) as error:
        print(f'Error de SIGECAP: {error}', file=sys.stderr)
        return 1
    except DatabaseError:
        print('Error de SQLite. Si otra instancia está trabajando, espera y vuelve a intentar. '
              'Si persiste, pide a soporte que revise el archivo y sus permisos.', file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print('\nOperación cancelada.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    if sys.argv[1:] not in (['instalar'], ['iniciar']):
        sys.exit('Ejecuta instalar.bat o iniciar.bat.')
    sys.exit(main(sys.argv[1]))
