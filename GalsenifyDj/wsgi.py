import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GalsenifyDj.settings')

# api/settings.py
WSGI_APPLICATION = 'api.wsgi.app'
