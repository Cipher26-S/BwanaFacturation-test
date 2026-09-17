"""Paramètres isolés pour exécuter la suite de tests sans PostgreSQL local."""
import os

os.environ.setdefault('SECRET_KEY', 'test-only-secret-key')

from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Aucun e-mail réel ne doit être envoyé par les tests.
DEBUG = True
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
