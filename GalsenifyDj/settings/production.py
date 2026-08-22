import os

from .base import *  # noqa

DEBUG = False

SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'

if SECURE_SSL_REDIRECT:
    SECURE_HSTS_SECONDS = 2592000

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

STATIC_ROOT = os.environ.get('STATIC_ROOT') or str(BASE_DIR / 'staticfiles')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT') or str(BASE_DIR / 'media')
