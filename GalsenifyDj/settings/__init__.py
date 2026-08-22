import os

from .base import *  # noqa

if os.environ.get('DJANGO_ENV', 'local') == 'production':
    from .production import *  # noqa
else:
    from .local import *  # noqa
