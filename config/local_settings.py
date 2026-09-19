"""Configuration locale de développement sans dépendance à PostgreSQL."""
import os

from .settings import *  # noqa: F401,F403

DEBUG = True
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:8000/BwanaFacturation').rstrip('/')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
