"""Browser tests only: shared in-memory SQLite, independent of application data."""
from .test_settings import *  # noqa: F403

DEBUG = True
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'file:sigecap-browser-tests?mode=memory&cache=shared',
    'OPTIONS': {'uri': True},
}}
