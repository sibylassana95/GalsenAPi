import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa

DEBUG = False

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY manquante : définissez la variable d'environnement SECRET_KEY en production."
    )

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS manquant : définissez les domaines servis (ex. galsenapi.lassanasiby.com)."
    )

# Derrière le proxy/SSL de cPanel : fait confiance à l'en-tête du protocole
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'

if SECURE_SSL_REDIRECT:
    SECURE_HSTS_SECONDS = 2592000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True



STATIC_ROOT = os.environ.get('STATIC_ROOT') or str(BASE_DIR / 'staticfiles')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT') or str(BASE_DIR / 'media')
