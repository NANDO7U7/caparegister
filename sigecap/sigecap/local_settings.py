"""Explicit loopback-only development profile; never use for deployment."""
import os
from pathlib import Path
from django.core.management.utils import get_random_secret_key

os.environ['SIGECAP_ENV'] = 'local'
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass
# Kept in the environment so the runserver reloader inherits the same key.
os.environ.setdefault('SECRET_KEY', get_random_secret_key())

from .settings import *  # noqa: E402,F403
