"""Validate environment configuration without opening any database."""
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key


def configuration(env, base_dir):
    mode = env.get('SIGECAP_ENV', 'production').lower()
    if mode not in {'local', 'test', 'production'}:
        raise ImproperlyConfigured('SIGECAP_ENV debe ser local, test o production.')
    local = mode == 'local'
    testing = mode == 'test'

    def required(name):
        value = env.get(name, '')
        if not value.strip():
            raise ImproperlyConfigured(f'Falta la variable de entorno {name}.')
        return value

    def boolean(name, default):
        value = env.get(name, str(default)).lower()
        if value not in {'true', 'false', '1', '0'}:
            raise ImproperlyConfigured(f'{name} debe ser True o False.')
        return value in {'true', '1'}

    debug = False if testing else boolean('DEBUG', local)
    if not local and debug:
        raise ImproperlyConfigured('DEBUG solo puede habilitarse en el perfil local.')
    secret = get_random_secret_key() if testing else env.get('SECRET_KEY', '')
    if not secret and local:
        secret = get_random_secret_key()
    if len(secret) < 50 or len(set(secret)) < 5 or secret.startswith('django-insecure-'):
        raise ImproperlyConfigured('Configura SECRET_KEY con una clave aleatoria de al menos 50 caracteres.')

    hosts = ['testserver', 'localhost', '127.0.0.1', '[::1]'] if testing else [
        host.strip() for host in env.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]' if local else '').split(',')
        if host.strip()
    ]
    if not hosts or any('*' in host or '://' in host or '/' in host for host in hosts):
        raise ImproperlyConfigured('ALLOWED_HOSTS debe contener hosts explícitos sin comodines.')
    if local and not set(hosts) <= {'localhost', '127.0.0.1', '[::1]'}:
        raise ImproperlyConfigured('El perfil local solo admite hosts de loopback.')

    engine = env.get('DB_ENGINE', 'django.db.backends.sqlite3' if local else 'django.db.backends.postgresql')
    if boolean('USE_POSTGRES', False):
        engine = 'django.db.backends.postgresql'
    if testing:
        database = {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
    elif engine == 'django.db.backends.postgresql':
        database = {'ENGINE': engine, **{
            key: required('DB_' + key) for key in ('NAME', 'USER', 'PASSWORD', 'HOST')
        }, 'PORT': env.get('DB_PORT', '5432')}
    elif engine == 'django.db.backends.sqlite3':
        name = env.get('DB_NAME', str(Path(base_dir) / 'db.sqlite3')) if local else required('DB_NAME')
        database = {'ENGINE': engine, 'NAME': name}
    else:
        raise ImproperlyConfigured('DB_ENGINE no admitido.')

    return {
        'SIGECAP_ENV': mode, 'SECRET_KEY': secret, 'DEBUG': debug, 'ALLOWED_HOSTS': hosts,
        'DATABASES': {'default': database},
        'SESSION_COOKIE_SECURE': not (local or testing),
        'CSRF_COOKIE_SECURE': not (local or testing),
        'SECURE_SSL_REDIRECT': not (local or testing),
        'SECURE_HSTS_SECONDS': 3600 if mode == 'production' else 0,
    }
