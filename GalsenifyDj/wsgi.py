import os
from django.core.wsgi import get_wsgi_application

# Assurez-vous que le nom du module de paramètres est correct
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GalsenifyDj.settings')

# Cette ligne crée l'application WSGI que Vercel utilisera
application = get_wsgi_application()
