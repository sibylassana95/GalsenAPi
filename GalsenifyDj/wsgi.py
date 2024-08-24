import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GalsenifyDj.settings')

# Exposez l'application Django WSGI en tant que `app`
app = get_wsgi_application()

# Pour être sûr que Vercel trouve la variable, vous pouvez aussi la nommer `handler`
handler = app
