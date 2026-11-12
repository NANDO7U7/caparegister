"""Isolated test database; never reads or writes the local application database."""
import os

os.environ['SIGECAP_ENV'] = 'test'

from .settings import *  # noqa: F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
